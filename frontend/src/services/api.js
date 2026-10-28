const BASE_URL = (import.meta.env.VITE_API_URL ?? 'http://localhost:8000').replace(/\/$/, '')
const TOKEN_KEY = 'aquadata_token'

export const tokenStorage = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (token) => localStorage.setItem(TOKEN_KEY, token),
  clear: () => localStorage.removeItem(TOKEN_KEY),
}

let onUnauthorized = () => {}
export function setUnauthorizedHandler(handler) {
  onUnauthorized = handler
}

export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.status = status
  }
}

function extractMessage(data, fallback) {
  const detail = data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail.map((e) => String(e.msg).replace(/^Value error, /, '')).join('; ')
  }
  return fallback
}

export async function request(path, { method = 'GET', body, form, auth = true } = {}) {
  const headers = {}
  const token = tokenStorage.get()
  if (auth && token) headers.Authorization = `Bearer ${token}`

  let payload
  if (form) {
    headers['Content-Type'] = 'application/x-www-form-urlencoded'
    payload = new URLSearchParams(form)
  } else if (body !== undefined) {
    headers['Content-Type'] = 'application/json'
    payload = JSON.stringify(body)
  }

  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, { method, headers, body: payload })
  } catch {
    throw new ApiError(0, 'Não foi possível conectar ao servidor')
  }

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    if (response.status === 401 && auth && token) onUnauthorized()
    throw new ApiError(response.status, extractMessage(data, 'Erro inesperado'))
  }
  return data
}