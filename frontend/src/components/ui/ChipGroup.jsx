export default function ChipGroup({ options, value, onChange, ariaLabel }) {
  return (
    <div role="group" aria-label={ariaLabel} className="flex flex-wrap gap-2">
      {options.map((option) => {
        const selected = option.value === value
        return (
          <button
            key={option.value}
            type="button"
            aria-pressed={selected}
            onClick={() => onChange(option.value)}
            className={`h-11 rounded-xl border px-4 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-text ${
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