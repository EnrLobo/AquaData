import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { formatDecimal } from '../utils/session'

function ChartTooltip({ active, payload, metric }) {
  if (!active || !payload?.length) return null
  const point = payload[0].payload
  if (point.value == null) return null
  return (
    <div className="rounded-xl border border-line bg-surface px-3 py-2 text-sm shadow-md">
      <p className="text-xs text-muted">{point.label}</p>
      {point.detail && <p className="text-xs text-muted">{point.detail}</p>}
      <p className="font-semibold">
        {formatDecimal(point.value, metric.digits)} {metric.unit}
      </p>
    </div>
  )
}

// trend: { start, end, first_index, last_index } da regressão linear (opcional)
export default function MetricChart({ data, metric, currentIndex = -1, trend = null }) {
  const current = currentIndex >= 0 ? data[currentIndex] : undefined
  const tick = { fill: 'var(--muted)', fontSize: 12 }

  return (
    <div
      role="img"
      aria-label={`Gráfico de ${metric.label} em ${data.length} treinos${
        trend ? ', com linha de tendência' : ''
      }`}
      className="h-72 w-full"
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 16, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid stroke="var(--line)" vertical={false} />
          <XAxis
            dataKey="x"
            type="number"
            domain={[0, Math.max(data.length - 1, 0)]}
            allowDecimals={false}
            tickFormatter={(x) => data[x]?.label ?? ''}
            tick={tick}
            stroke="var(--line)"
            tickLine={false}
            minTickGap={24}
          />
          <YAxis
            domain={['auto', 'auto']}
            tick={tick}
            width={48}
            tickFormatter={(v) => formatDecimal(v, metric.digits)}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip content={<ChartTooltip metric={metric} />} />
          {trend && (
            <ReferenceLine
              segment={[
                { x: trend.first_index, y: trend.start },
                { x: trend.last_index, y: trend.end },
              ]}
              stroke="var(--accent)"
              strokeWidth={2}
              strokeDasharray="6 4"
              ifOverflow="extendDomain"
            />
          )}
          <Line
            type="monotone"
            dataKey="value"
            stroke="var(--brand)"
            strokeWidth={2}
            dot={{ r: 3, fill: 'var(--brand)', stroke: 'var(--brand)' }}
            connectNulls
            isAnimationActive={false}
          />
          {current?.value != null && (
            <ReferenceDot
              x={current.x}
              y={current.value}
              r={6}
              fill="var(--surface)"
              stroke="var(--brand)"
              strokeWidth={3}
              ifOverflow="extendDomain"
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}