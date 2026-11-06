import { request } from './api'

export function listSessions({
  search,
  athleteId,
  sessionType,
  stroke,
  dateFrom,
  dateTo,
  limit = 10,
  offset = 0,
} = {}) {
  const params = new URLSearchParams({ limit, offset })
  if (search?.trim()) params.set('search', search.trim())
  if (athleteId) params.set('athlete_id', athleteId)
  if (sessionType) params.set('session_type', sessionType)
  if (stroke) params.set('stroke', stroke)
  if (dateFrom) params.set('date_from', dateFrom)
  if (dateTo) params.set('date_to', dateTo)
  return request(`/sessions?${params}`)
}

export function listAthleteSessions(athleteId, { stroke, limit = 200 } = {}) {
  const params = new URLSearchParams({ limit })
  if (stroke) params.set('stroke', stroke)
  return request(`/athletes/${athleteId}/sessions?${params}`)
}

export const getSession = (athleteId, id) => request(`/athletes/${athleteId}/sessions/${id}`)

export const createSession = (athleteId, data) =>
  request(`/athletes/${athleteId}/sessions`, { method: 'POST', body: data })

export const updateSession = (athleteId, id, data) =>
  request(`/athletes/${athleteId}/sessions/${id}`, { method: 'PUT', body: data })

export const deleteSession = (athleteId, id) =>
  request(`/athletes/${athleteId}/sessions/${id}`, { method: 'DELETE' })