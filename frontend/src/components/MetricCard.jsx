import { formatDecimal } from '../utils/session'
import Dash from './ui/Dash'

export default function MetricCard({ metric, value }) {
  return (
    <div className="rounded-2xl border border-line bg-surface p-5">
      <p className="text-sm text-muted">{metric.label}</p>
      <p className="mt-2 text-3xl font-semibold tracking-tight">
        {value != null ? (
          <>
            {formatDecimal(value, metric.digits)}
            {metric.unit && (
              <span className="ml-1.5 text-base font-medium text-muted">{metric.unit}</span>
            )}
          </>
        ) : (
          <Dash />
        )}
      </p>
      <p className="mt-2 text-xs text-muted">{metric.description}</p>
    </div>
  )
}