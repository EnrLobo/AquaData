export default function TextField({
  label,
  id,
  hint,
  hideLabel = false,
  trailing,
  className = '',
  ...props
}) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={id} className={hideLabel ? 'sr-only' : 'text-sm font-medium text-fg'}>
        {label}
      </label>
      <div className="relative">
        <input
          id={id}
          className={`h-11 w-full rounded-xl border border-accent/40 bg-bg px-4 text-sm text-fg placeholder:text-muted focus:border-brand focus:outline-2 focus:outline-accent/40 ${
            trailing ? 'pr-12' : ''
          } ${className}`}
          {...props}
        />
        {trailing && <div className="absolute inset-y-0 right-1.5 flex items-center">{trailing}</div>}
      </div>
      {hint && <p className="text-xs text-muted">{hint}</p>}
    </div>
  )
}