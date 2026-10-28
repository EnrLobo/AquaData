import { request, tokenStorage } from './api'

export async function login(email, password) {
  const data = await request('/auth/login', {
    method: 'POST',
    form: { username: email, password },
    auth: false,
  })
  tokenStorage.set(data.access_token)
  return request('/auth/me')
}

export const fetchMe = () => request('/auth/me')
export const logout = () => tokenStorage.clear()
export const register = (payload) =>
  request('/auth/register', { method: 'POST', body: payload, auth: false })