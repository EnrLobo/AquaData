export const STROKE_LABEL = {
  freestyle: 'Livre',
  backstroke: 'Costas',
  breaststroke: 'Peito',
  butterfly: 'Borboleta',
  medley: 'Medley',
}

export const SESSION_TYPE_LABEL = {
  training: 'Treino',
  competition: 'Competição',
}

export const formatRace = (session) => `${session.distance_m}m ${STROKE_LABEL[session.stroke]}`

export const formatDecimal = (value, digits = 2) => value.toFixed(digits).replace('.', ',')

// 29.38 -> 0:29,38 | 64.62 -> 1:04,62
export function formatTime(seconds) {
  const cs = Math.round(seconds * 100)
  const minutes = Math.floor(cs / 6000)
  const rest = cs % 6000
  const ss = String(Math.floor(rest / 100)).padStart(2, '0')
  const cc = String(rest % 100).padStart(2, '0')
  return `${minutes}:${ss},${cc}`
}

export function parseInteger(text) {
  const value = text.trim()
  if (!/^\d+$/.test(value)) return null
  const n = Number(value)
  return n > 0 ? n : null
}

export function parseDecimal(text) {
  const value = text.trim().replace(',', '.')
  if (!/^\d+(\.\d{1,2})?$/.test(value)) return null
  const n = Number(value)
  return n > 0 ? n : null
}

// aceita 29,38 | 1:02,45 | 62.45 e devolve segundos
export function parseTime(text) {
  const match = /^(?:(\d{1,3}):)?(\d{1,3}(?:[.,]\d{1,2})?)$/.exec(text.trim())
  if (!match) return null
  const hasMinutes = match[1] !== undefined
  const seconds = Number(match[2].replace(',', '.'))
  if (hasMinutes && seconds >= 60) return null
  const total = Math.round(((hasMinutes ? Number(match[1]) : 0) * 60 + seconds) * 100) / 100
  return total > 0 ? total : null
}

export const METRICS = [
  { key: 'vn', short: 'VN', label: 'Velocidade de nado (VN)', unit: 'm/s', digits: 2, better: 'up',
    description: 'Distância do trecho de nado puro ÷ tempo do trecho' },
  { key: 'cb', short: 'CB', label: 'Comprimento de braçada (CB)', unit: 'm', digits: 2, better: 'up',
    description: 'Distância percorrida a cada ciclo de braçada' },
  { key: 'cn', short: 'Cadência', label: 'Cadência (CN)', unit: 'ciclos/min', digits: 1, better: null,
    description: 'Ciclos de braçada por minuto no trecho de nado puro' },
  { key: 'swim_index', short: 'IN', label: 'Índice de nado (IN)', unit: 'm²/s', digits: 2, better: 'up',
    description: 'CB × VN: eficiência global do nado' },
  { key: 'vm', short: 'Vm', label: 'Velocidade média (Vm)', unit: 'm/s', digits: 2, better: 'up',
    description: 'Distância total ÷ tempo total, com saída e viradas' },
  { key: 'swolf', short: 'SWOLF', label: 'SWOLF', unit: '', digits: 1, better: 'down',
    description: 'Tempo total (s) + braçadas da prova completa (não calculado no medley)' },
  { key: 'swolf_25', short: 'SWOLF 25 m', label: 'SWOLF a cada 25 m', unit: '', digits: 1, better: 'down',
    description: 'SWOLF proporcional a 25 m: compara provas e piscinas na mesma escala' },
]

export const BETTER_HINT = { up: 'Quanto maior, melhor.', down: 'Quanto menor, melhor.' }