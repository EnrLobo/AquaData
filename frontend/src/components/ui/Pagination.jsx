import { ChevronLeft, ChevronRight } from 'lucide-react'

function pageWindow(page, total, size = 5) {
  const end = Math.min(total, Math.max(1, page - 2) + size - 1)
  const start = Math.max(1, end - size + 1)
  return Array.from({ length: end - start + 1 }, (_, i) => start + i)
}

const box =
  'grid size-9 place-items-center rounded-lg border text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-text disabled:pointer-events-none disabled:opacity-40'

export default function Pagination({ page, totalPages, onChange }) {
  if (totalPages <= 1) return null

  return (
    <nav aria-label="Paginação" className="flex items-center gap-1.5">
      <button
        type="button"
        className={`${box} border-line bg-surface text-muted hover:bg-subtle`}
        disabled={page === 1}
        onClick={() => onChange(page - 1)}
        aria-label="Página anterior"
      >
        <ChevronLeft size={16} aria-hidden="true" />
      </button>
      {pageWindow(page, totalPages).map((n) => (
        <button
          key={n}
          type="button"
          onClick={() => onChange(n)}
          aria-label={`Ir para a página ${n}`}
          aria-current={n === page ? 'page' : undefined}
          className={`${box} ${
            n === page
              ? 'border-brand bg-brand text-brand-fg'
              : 'border-line bg-surface text-fg hover:bg-subtle'
          }`}
        >
          {n}
        </button>
      ))}
      <button
        type="button"
        className={`${box} border-line bg-surface text-muted hover:bg-subtle`}
        disabled={page === totalPages}
        onClick={() => onChange(page + 1)}
        aria-label="Próxima página"
      >
        <ChevronRight size={16} aria-hidden="true" />
      </button>
    </nav>
  )
}