import { request } from './api'

export function getReport(athleteId, { dateFrom, dateTo } = {}) {
  const params = new URLSearchParams()
  if (dateFrom) params.set('date_from', dateFrom)
  if (dateTo) params.set('date_to', dateTo)
  const query = params.toString()
  return request(`/athletes/${athleteId}/report${query ? `?${query}` : ''}`)
}