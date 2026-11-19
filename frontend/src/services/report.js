import { request, requestFile } from './api'

function periodQuery({ dateFrom, dateTo } = {}) {
  const params = new URLSearchParams()
  if (dateFrom) params.set('date_from', dateFrom)
  if (dateTo) params.set('date_to', dateTo)
  const query = params.toString()
  return query ? `?${query}` : ''
}

export function getReport(athleteId, period) {
  return request(`/athletes/${athleteId}/report${periodQuery(period)}`)
}

export function getReportCsv(athleteId, period) {
  return requestFile(`/athletes/${athleteId}/report/csv${periodQuery(period)}`)
}