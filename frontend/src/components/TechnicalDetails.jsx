import { ChevronRight } from 'lucide-react'

// Área recolhida com os termos estatísticos (AQ-26): a tela mostra a explicação em
// linguagem simples, e quem quiser conferir os números do modelo abre aqui.
export default function TechnicalDetails({ title = 'Detalhes técnicos', children, className = '' }) {
  return (
    <details className={`group rounded-xl border border-line text-sm print:hidden ${className}`}>
      <summary className="flex cursor-pointer list-none items-center gap-1.5 px-4 py-3 text-xs font-medium text-muted hover:text-fg">
        <ChevronRight
          size={14}
          aria-hidden="true"
          className="transition-transform group-open:rotate-90 motion-reduce:transition-none"
        />
        {title}
      </summary>
      <div className="border-t border-line px-4 py-3 text-xs text-muted">{children}</div>
    </details>
  )
}