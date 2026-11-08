export function formatDate(iso) {
  const [year, month, day] = iso.split('-')
  return `${day}/${month}/${year}`
}

export function calcAge(iso) {
  const [year, month, day] = iso.split('-').map(Number)
  const today = new Date()
  let age = today.getFullYear() - year
  const beforeBirthday =
    today.getMonth() + 1 < month || (today.getMonth() + 1 === month && today.getDate() < day)
  if (beforeBirthday) age -= 1
  return age
}

function toIso(d) {
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${month}-${day}`
}

export function todayIso() {
  return toIso(new Date())
}

// data de N dias atrás (no fuso do navegador), no formato AAAA-MM-DD
export function isoDaysAgo(days) {
  const d = new Date()
  d.setDate(d.getDate() - days)
  return toIso(d)
}

export function formatShortDate(iso) {
  const [year, month, day] = iso.split('-')
  return `${day}/${month}/${year.slice(2)}`
}

export function daysSince(iso) {
  const [year, month, day] = iso.split('-').map(Number)
  const today = new Date()
  const start = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const then = new Date(year, month - 1, day)
  return Math.round((start - then) / 86400000)
}

export function formatDaysAgo(iso) {
  const days = daysSince(iso)
  if (days <= 0) return 'hoje'
  if (days === 1) return 'ontem'
  return `há ${days} dias`
}