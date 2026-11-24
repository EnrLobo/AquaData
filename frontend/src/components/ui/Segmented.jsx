// Grupo de opções exclusivas. No celular, os botões ficam mais altos (área de toque) e,
// se não couberem, o grupo rola para o lado em vez de estourar a tela (AQ-26).
export default function Segmented({ options, value, onChange, ariaLabel, className = '' }) {
  return (
    <div
      role="radiogroup"
      aria-label={ariaLabel}
      className={`scroll-x-hidden inline-flex max-w-full overflow-x-auto rounded-lg border border-line bg-subtle p-1 ${className}`}
    >
      {options.map((option) => {
        const selected = option.value === value
        return (
          <button
            key={String(option.value)}
            type="button"
            role="radio"
            aria-checked={selected}
            onClick={() => onChange(option.value)}
            className={`h-10 shrink-0 whitespace-nowrap rounded-md px-3 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-brand-text sm:h-8 ${
              selected ? 'bg-bg text-fg shadow-sm' : 'text-muted hover:text-fg'
            }`}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}