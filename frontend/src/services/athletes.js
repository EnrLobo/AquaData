import { request } from './api'

export function listAthletes({ active, search, limit = 50, offset = 0 } = {}) {
  const params = new URLSearchParams({ limit, offset })
  if (active !== undefined && active !== null) params.set('active', active)
  if (search?.trim()) params.set('search', search.trim())
  return request(`/athletes?${params}`)
}

export const getAthlete = (id) => request(`/athletes/${id}`)
export const createAthlete = (data) => request('/athletes', { method: 'POST', body: data })
export const updateAthlete = (id, data) =>
  request(`/athletes/${id}`, { method: 'PATCH', body: data })