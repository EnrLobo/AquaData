import { Loader2 } from 'lucide-react'

export default function Spinner({ label = 'Carregando' }) {
  return (
    <div role="status" className="flex items-center justify-center gap-2 py-16 text-muted">
      <Loader2 className="animate-spin" size={18} aria-hidden="true" />
      <span className="text-sm">{label}…</span>
    </div>
  )
}