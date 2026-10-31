const base =
  'inline-flex items-center justify-center gap-2 rounded-xl text-sm font-medium transition-colors ' +
  'focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-text ' +
  'disabled:pointer-events-none disabled:opacity-50'

const variants = {
  primary: 'bg-brand text-brand-fg hover:bg-brand-hover',
  secondary: 'border border-line bg-surface text-fg hover:bg-subtle',
  ghost: 'text-muted hover:bg-subtle hover:text-fg',
  danger: 'border border-line text-danger hover:bg-danger-soft',
}

const sizes = { md: 'h-11 px-5', sm: 'h-8 px-3', icon: 'size-9' }

export function buttonClasses(variant = 'primary', size = 'md', extra = '') {
  return [base, variants[variant], sizes[size], extra].filter(Boolean).join(' ')
}