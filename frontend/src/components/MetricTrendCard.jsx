import { Minus, TrendingDown, TrendingUp } from 'lucide-react'
import { formatDecimal } from '../utils/session'
import Dash from './ui/Dash'

function signed(value, digits) {
  const sign = value > 0 ? '+' : value < 0 ? '−' : ''
  return `${sign}${formatDecimal(Math.abs(value), digits)}`
}

function trendWord(trend, improved) {
  if (improved === true) return 'tendência de melhora'
  if (improved === false) return 'tendência de piora'
  if (trend.slope > 0) return 'tendência de alta'
  if (trend.slope < 0) return 'tendência de queda'
  return 'estável'
}

export default function MetricTrendCard({ metric, summary, selected, onSelect }) {
  const trend = summary?.trend ?? null
  const Icon = !trend || trend.slope === 0 ? Minus : trend.slope > 0 ? TrendingUp : TrendingDown
  const tone =
    summary?.improved === true
      ? 'text-success'
      : summary?.improved === false
        ? 'text-danger'
        : 'text-muted'

  return (
    <button
      type="button"
      aria-pressed={selected}
      onClick={onSelect}
      title={metric.label}
      className={`rounded-2xl border bg-surface p-5 text-left transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-text ${
        selected ? 'border-brand ring-1 ring-brand' : 'border-line hover:bg-subtle'
      }`}
    >
      <p className="text-sm text-muted">{metric.label}</p>
      <p className="mt-2 text-2xl font-semibold tracking-tight">
        {summary ? (
          <>
            {formatDecimal(summary.last, metric.digits)}
            {metric.unit && (
              <span className="ml-1.5 text-sm font-medium text-muted">{metric.unit}</span>
            )}
          </>
        ) : (
          <Dash />
        )}
      </p>
      {trend ? (
        <p className={`mt-2 flex flex-wrap items-center gap-1.5 text-xs font-medium ${tone}`}>
          <Icon size={14} aria-hidden="true" />
          <span>
            {signed(trend.slope, metric.digits + 1)}
            {metric.unit ? ` ${metric.unit}` : ''} por treino
          </span>
          <span>· {trendWord(trend, summary.improved)}</span>
        </p>
      ) : (
        <p className="mt-2 text-xs text-muted">
          {summary ? 'Poucos treinos para indicar tendência (mínimo 3)' : 'Sem dados no período'}
        </p>
      )}
      {summary && (
        <p className="mt-1 text-xs text-muted">
          {summary.best != null ? `Melhor: ${formatDecimal(summary.best, metric.digits)} · ` : ''}
          Média: {formatDecimal(summary.mean, metric.digits)}
          {trend?.r2 != null && (
            <span title="Coeficiente de determinação: quanto a reta explica a variação (0 a 1)">
              {' '}
              · R² {formatDecimal(trend.r2, 2)}
            </span>
          )}
        </p>
      )}
    </button>
  )
}