import { Info } from 'lucide-react'
import { BETTER_HINT, METRICS } from '../utils/session'

// Legenda do gráfico: explica a métrica exibida e, sob demanda, todas as siglas.
export default function MetricLegend({ metric }) {
  return (
    <div className="mt-4 space-y-3 border-t border-line pt-4 text-sm">
      <p className="flex items-start gap-2">
        <Info size={16} aria-hidden="true" className="mt-0.5 shrink-0 text-brand-text" />
        <span>
          <strong className="font-semibold">{metric.label}</strong>
          {metric.unit ? ` (${metric.unit})` : ''}: {metric.description}.
          {metric.better ? ` ${BETTER_HINT[metric.better]}` : ' Não há sentido fixo de melhora.'}
        </span>
      </p>
      <details>
        <summary className="cursor-pointer font-medium text-brand-text hover:underline">
          O que significa cada sigla
        </summary>
        <dl className="mt-3 grid gap-x-8 gap-y-3 sm:grid-cols-2">
          {METRICS.map((m) => (
            <div key={m.key}>
              <dt className="font-medium">
                {m.label}
                {m.unit && <span className="font-normal text-muted"> · {m.unit}</span>}
              </dt>
              <dd className="mt-0.5 text-xs text-muted">
                {m.description}.{' '}
                {m.better ? BETTER_HINT[m.better] : 'Não há sentido fixo de melhora.'}
              </dd>
            </div>
          ))}
        </dl>
      </details>
    </div>
  )
}