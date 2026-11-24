// Grupo de chips. Com scroll, no celular os chips ficam numa linha que rola para o lado
// (em vez de ocupar várias linhas da tela); a partir de sm, quebram linha normalmente (AQ-26).
export default function ChipGroup({ options, value, onChange, ariaLabel, scroll = false }) {
  const layout = scroll
    ? 'scroll-x-hidden -mx-1 flex max-w-full gap-2 overflow-x-auto px-1 pb-1 sm:mx-0 sm:flex-wrap sm:overflow-visible sm:px-0 sm:pb-0'
    : 'flex flex-wrap gap-2'
  return (
    <div role="group" aria-label={ariaLabel} className={layout}>
      {options.map((option) => {
        const selected = option.value === value
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={selected}
            title={option.title}
            onClick={() => onChange(option.value)}
            className={`h-11 shrink-0 whitespace-nowrap rounded-xl border px-4 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-text ${
              selected
                ? 'border-brand bg-brand text-brand-fg'
                : 'border-line bg-surface text-fg hover:bg-subtle'
            }`}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}