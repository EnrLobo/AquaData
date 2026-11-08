import { request } from './api'

export function getPerformance(
  athleteId,
  { stroke, distance, pool, sessionType, dateFrom, dateTo } = {},
) {
  const params = new URLSearchParams()
  if (stroke) params.set('stroke', stroke)
  if (distance) params.set('distance_m', distance)
  if (pool) params.set('pool_length_m', pool)
  if (sessionType) params.set('session_type', sessionType)
  if (dateFrom) params.set('date_from', dateFrom)
  if (dateTo) params.set('date_to', dateTo)
  const query = params.toString()
  return request(`/athletes/${athleteId}/performance${query ? `?${query}` : ''}`)
}