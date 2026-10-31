import { Search } from 'lucide-react'

export default function SearchField({ id, label, className = '', ...props }) {
  return (
    <div className={`relative ${className}`}>
      <label htmlFor={id} className="sr-only">
        {label}
      </label>
      <Search
        size={18}
        aria-hidden="true"
        className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-muted"
      />
      <input
        id={id}
        type="search"
        className="h-11 w-full rounded-xl border border-line bg-surface pl-11 pr-4 text-sm text-fg placeholder:text-muted focus:border-brand focus:outline-2 focus:outline-accent/40"
        {...props}
      />
    </div>
  )
}