import { request } from './api'

export function getPrediction(athleteId, { stroke, distance, pool }) {
  const params = new URLSearchParams({
    stroke,
    distance_m: String(distance),
    pool_length_m: String(pool),
  })
  return request(`/athletes/${athleteId}/prediction?${params.toString()}`)
}