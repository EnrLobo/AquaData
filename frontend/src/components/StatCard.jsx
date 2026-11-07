export default function StatCard({ icon: Icon, label, value, hint, tone = 'default' }) {
  const toneClass =
    tone === 'warning' ? 'bg-warning-soft text-warning' : 'bg-brand-soft text-brand-text'

  return (
    <div className="rounded-2xl border border-line bg-surface p-5">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-muted">{label}</p>
        <span aria-hidden="true" className={`grid size-9 place-items-center rounded-full ${toneClass}`}>
          <Icon size={18} />
        </span>
      </div>
      <p className="mt-3 text-3xl font-semibold tracking-tight">{value}</p>
      {hint && <p className="mt-1 text-xs text-muted">{hint}</p>}
    </div>
  )
}