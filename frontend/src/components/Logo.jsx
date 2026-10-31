import logoUrl from '../assets/logo.svg'

export default function Logo({ className = 'h-9' }) {
  return (
    <img
      src={logoUrl}
      alt="aquaData"
      className={`w-auto dark:brightness-0 dark:invert ${className}`}
    />
  )
}