import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { formatDecimal } from '../utils/session'

const COMPETITION_COLOR = 'var(--warning)'

function ChartTooltip({ active, payload, metric, lines, format }) {
  if (!active || !payload?.length) return null
  const point = payload[0].payload
  const rows = [
    point.value != null && { name: point.isCompetition ? 'Real (competição)' : 'Real', value: point.value },
    ...lines.map((l) => point[l.dataKey] != null && { name: l.name, value: point[l.dataKey] }),
  ].filter(Boolean)
  if (!rows.length) return null
  return (
    <div className="rounded-xl border border-line bg-surface px-3 py-2 text-sm shadow-md">
      <p className="text-xs text-muted">{point.label}</p>
      {point.detail && <p className="text-xs text-muted">{point.detail}</p>}
      {rows.map((row) => (
        <p key={row.name} className={rows.length > 1 ? 'mt-0.5' : 'font-semibold'}>
          {rows.length > 1 && <span className="text-muted">{row.name}: </span>}
          <span className="font-semibold">
            {format(row.value)}
            {metric.unit && metric.unit !== 's' ? ` ${metric.unit}` : ''}
          </span>
        </p>
      ))}
    </div>
  )
}

function ValueDot({ cx, cy, payload }) {
  if (cx == null || cy == null || payload.value == null) return null
  const color = payload.isCompetition ? COMPETITION_COLOR : 'var(--brand)'
  return <circle cx={cx} cy={cy} r={payload.isCompetition ? 4.5 : 3} fill={color} stroke={color} />
}

/**
 * Gráfico de evolução.
 * - data: [{ x, label, detail?, value, isCompetition?, ...linhas extras }]
 * - trend: { start, end, first_index, last_index } (linha de tendência opcional)
 * - lines: linhas extras [{ dataKey, name, color, dashed }]
 * - futureFrom: x a partir do qual os pontos são projeção (área "Previsão")
 * - format: formatação dos valores (padrão: decimal com metric.digits)
 */
export default function MetricChart({
  data,
  metric,
  currentIndex = -1,
  trend = null,
  lines = [],
  futureFrom = null,
  format = null,
}) {
  const current = currentIndex >= 0 ? data[currentIndex] : undefined
  const tick = { fill: 'var(--muted)', fontSize: 12 }
  const formatValue = format ?? ((v) => formatDecimal(v, metric.digits))
  const lastX = Math.max(data.length - 1, 0)

  return (
    <div>
      <div
        role="img"
        aria-label={`Gráfico de ${metric.label} em ${data.length} pontos${
          trend ? ', com linha de tendência' : ''
        }${futureFrom != null ? ', com projeção dos próximos registros' : ''}`}
        className="h-60 w-full sm:h-72"
      >
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 16, right: 8, bottom: 0, left: 0 }}>
            <CartesianGrid stroke="var(--line)" vertical={false} />
            {futureFrom != null && futureFrom <= lastX && (
              <ReferenceArea
                x1={futureFrom - 0.5}
                x2={lastX}
                fill="var(--subtle)"
                fillOpacity={0.8}
                ifOverflow="extendDomain"
                label={{
                  value: 'Previsão',
                  position: 'insideTop',
                  fill: 'var(--muted)',
                  fontSize: 12,
                }}
              />
            )}
            <XAxis
              dataKey="x"
              type="number"
              domain={[0, lastX]}
              allowDecimals={false}
              padding={{ left: 16, right: 16 }}
              interval="preserveStartEnd"
              tickFormatter={(x) => data[x]?.label ?? ''}
              tick={tick}
              stroke="var(--line)"
              tickLine={false}
              tickMargin={8}
              minTickGap={32}
            />
            <YAxis
              domain={['auto', 'auto']}
              tick={tick}
              width={format ? 64 : 48}
              tickFormatter={formatValue}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip
              content={<ChartTooltip metric={metric} lines={lines} format={formatValue} />}
            />
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
            {lines.map((l) => (
              <Line
                key={l.dataKey}
                type="linear"
                dataKey={l.dataKey}
                name={l.name}
                stroke={l.color}
                strokeWidth={2}
                strokeDasharray={l.dashed ? '6 4' : undefined}
                dot={false}
                connectNulls
                isAnimationActive={false}
              />
            ))}
            <Line
              type="monotone"
              dataKey="value"
              stroke="var(--brand)"
              strokeWidth={2}
              dot={<ValueDot />}
              activeDot={{ r: 5 }}
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
      {lines.length > 0 && (
        <ul className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs text-muted">
          <li className="flex items-center gap-1.5">
            <span aria-hidden="true" className="inline-block size-2.5 rounded-full bg-brand" />
            Treino real
          </li>
          {data.some((d) => d.isCompetition) && (
            <li className="flex items-center gap-1.5">
              <span aria-hidden="true" className="inline-block size-2.5 rounded-full bg-warning" />
              Competição real
            </li>
          )}
          {lines.map((l) => (
            <li key={l.dataKey} className="flex items-center gap-1.5">
              <span
                aria-hidden="true"
                className="inline-block w-4 border-t-2 border-dashed"
                style={{ borderColor: l.color }}
              />
              {l.name}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}