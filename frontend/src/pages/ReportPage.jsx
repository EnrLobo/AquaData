import {
  Activity,
  ArrowRight,
  CalendarRange,
  Info,
  Layers,
  Medal,
  Minus,
  Timer,
  TrendingDown,
  TrendingUp,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import MetricChart from '../components/MetricChart'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Alert from '../components/ui/Alert'
import Badge from '../components/ui/Badge'
import { buttonClasses } from '../components/ui/button-styles'
import Dash from '../components/ui/Dash'
import Segmented from '../components/ui/Segmented'
import Select from '../components/ui/Select'
import Spinner from '../components/ui/Spinner'
import { listAthletes } from '../services/athletes'
import { getReport } from '../services/report'
import { calcAge, formatDate, formatShortDate, isoDaysAgo } from '../utils/date'
import {
  METRICS,
  SESSION_TYPE_LABEL,
  STROKE_LABEL,
  TIME_METRIC,
  formatDecimal,
  formatTime,
} from '../utils/session'

const PERIOD_OPTIONS = [
  { value: '30', label: '30 dias' },
  { value: '90', label: '90 dias' },
  { value: '365', label: '12 meses' },
  { value: '', label: 'Tudo' },
]

const SEX_LABEL = { M: 'Masculino', F: 'Feminino' }

// selo da tendência prevista (mesmo do Início)
const STATUS = {
  improving: { label: 'Melhorando', tone: 'success' },
  stable: { label: 'Estável', tone: 'neutral' },
  attention: { label: 'Atenção', tone: 'warning' },
}

const MODEL_LINES = {
  training: { dataKey: 'model', name: 'Modelo (treino)', color: 'var(--accent)', dashed: true },
  competition: {
    dataKey: 'modelComp',
    name: 'Modelo (competição)',
    color: 'var(--warning)',
    dashed: true,
  },
}

function signed(value, digits = 2) {
  const sign = value > 0 ? '+' : value < 0 ? '−' : ''
  return `${sign}${formatDecimal(Math.abs(value), digits)}`
}

const eventTitle = (e) => `${e.distance_m} m ${STROKE_LABEL[e.stroke]}`

function readPeriod(params) {
  const period = params.get('periodo') ?? ''
  return PERIOD_OPTIONS.some((o) => o.value === period) ? period : ''
}

function Card({ title, children, className = '' }) {
  return (
    <div className={`rounded-xl border border-line bg-canvas p-4 ${className}`}>
      <p className="text-xs font-semibold uppercase tracking-wide text-muted">{title}</p>
      {children}
    </div>
  )
}

function Row({ label, children }) {
  return (
    <div className="mt-2 flex items-baseline justify-between gap-3 text-sm">
      <dt className="text-muted">{label}</dt>
      <dd className="text-right font-medium">{children}</dd>
    </div>
  )
}

function TimesCard({ event }) {
  const { time, best, last } = event
  return (
    <Card title="Tempos no período">
      <dl>
        <Row label="Melhor">
          <span className="font-semibold">{formatTime(best.time_s)}</span>
          <span className="block text-xs font-normal text-muted">
            {formatDate(best.session_date)} · {SESSION_TYPE_LABEL[best.session_type]}
          </span>
        </Row>
        <Row label="Último">
          {formatTime(last.time_s)}
          <span className="block text-xs font-normal text-muted">
            {formatDate(last.session_date)} · {SESSION_TYPE_LABEL[last.session_type]}
          </span>
        </Row>
        <Row label="Média">{formatTime(time.mean)}</Row>
        <Row label="Do primeiro ao último">
          {time.count > 1 ? `${signed(time.change)} s` : <Dash />}
        </Row>
      </dl>
    </Card>
  )
}

function PredictionCard({ event, minRecords, minTrendRecords }) {
  const p = event.prediction
  if (!p.available) {
    return (
      <Card title="Previsão do próximo registro">
        <p className="mt-3 flex items-start gap-2 text-sm text-muted">
          <Info size={16} aria-hidden="true" className="mt-0.5 shrink-0" />
          A previsão aparece a partir de {minRecords} registros desta prova (há {event.n_history}).
        </p>
      </Card>
    )
  }
  const status = p.status ? STATUS[p.status] : null
  return (
    <Card title="Previsão do próximo registro">
      <dl>
        <Row label="Se for treino">
          <span className="font-semibold">
            {p.training_s != null ? formatTime(p.training_s) : <Dash />}
          </span>
        </Row>
        <Row label="Se for competição">
          {p.competition_s != null ? formatTime(p.competition_s) : <Dash />}
        </Row>
        <Row label="Tendência">
          {status ? (
            <Badge tone={status.tone}>{status.label}</Badge>
          ) : (
            <Badge tone="neutral">
              Poucos registros ({event.n_history} de {minTrendRecords})
            </Badge>
          )}
          <span className="block text-xs font-normal text-muted">
            {signed(p.coef_order)} s por registro
          </span>
        </Row>
        <Row label="Erro médio do modelo (MAE)">
          {p.mae_s != null ? `${formatDecimal(p.mae_s, 2)} s` : <Dash />}
        </Row>
      </dl>
    </Card>
  )
}

function trendText(summary, minConclusive) {
  if (!summary.conclusive) return `poucos treinos (${summary.count} de ${minConclusive})`
  if (summary.improved === true) return 'melhora'
  if (summary.improved === false) return 'piora'
  if (summary.trend.slope > 0) return 'alta'
  if (summary.trend.slope < 0) return 'queda'
  return 'estável'
}

function MetricsTable({ event, minConclusive }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[40rem] text-left text-sm">
        <caption className="sr-only">Métricas de {eventTitle(event)} no período</caption>
        <thead className="text-xs uppercase tracking-wide text-muted">
          <tr>
            <th scope="col" className="py-2 pr-4 font-medium">Métrica</th>
            <th scope="col" className="py-2 pr-4 font-medium">Último</th>
            <th scope="col" className="py-2 pr-4 font-medium">Melhor</th>
            <th scope="col" className="py-2 pr-4 font-medium">Média</th>
            <th scope="col" className="py-2 font-medium">Tendência por treino</th>
          </tr>
        </thead>
        <tbody>
          {METRICS.map((m) => {
            const s = event.metrics[m.key]
            const unit = m.unit ? ` ${m.unit}` : ''
            const conclusive = Boolean(s?.trend && s.conclusive)
            const tone = !conclusive
              ? 'text-muted'
              : s.improved === true
                ? 'text-success'
                : s.improved === false
                  ? 'text-danger'
                  : 'text-muted'
            const Icon =
              !s?.trend || s.trend.slope === 0
                ? Minus
                : s.trend.slope > 0
                  ? TrendingUp
                  : TrendingDown
            return (
              <tr key={m.key} className="border-t border-line">
                <th scope="row" className="py-2 pr-4 font-medium" title={m.label}>
                  {m.short}
                </th>
                <td className="py-2 pr-4">
                  {s ? `${formatDecimal(s.last, m.digits)}${unit}` : <Dash />}
                </td>
                <td className="py-2 pr-4">
                  {s?.best != null ? `${formatDecimal(s.best, m.digits)}${unit}` : <Dash />}
                </td>
                <td className="py-2 pr-4">
                  {s ? `${formatDecimal(s.mean, m.digits)}${unit}` : <Dash />}
                </td>
                <td className={`py-2 ${tone}`}>
                  {s?.trend ? (
                    <span className="inline-flex flex-wrap items-center gap-1.5">
                      {conclusive && <Icon size={14} aria-hidden="true" />}
                      {signed(s.trend.slope, m.digits + 1)}
                      {unit} · {trendText(s, minConclusive)}
                    </span>
                  ) : (
                    <span className="text-muted">menos de 3 treinos</span>
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

function EventSection({ athleteId, event, report }) {
  const chartData = useMemo(() => {
    let future = 0
    return event.chart.map((p, i) => {
      const isFuture = p.session_date == null
      if (isFuture) future += 1
      return {
        x: i,
        label: isFuture ? `Próx. ${future}` : formatShortDate(p.session_date),
        detail: isFuture
          ? `Previsão do ${p.order}º registro da prova`
          : `${SESSION_TYPE_LABEL[p.session_type]} · ${p.order}º registro da prova`,
        value: p.time_s,
        isCompetition: p.session_type === 'competition',
        model: p.model_training_s,
        modelComp: p.model_competition_s,
      }
    })
  }, [event])

  const hasModel = event.chart.some((p) => p.model_training_s != null)
  const lines = hasModel
    ? [
        MODEL_LINES.training,
        ...(event.chart.some((p) => p.model_competition_s != null)
          ? [MODEL_LINES.competition]
          : []),
      ]
    : []
  const futureFrom = hasModel ? event.chart.findIndex((p) => p.session_date == null) : -1
  const headingId = `event-${event.stroke}-${event.distance_m}-${event.pool_length_m}`

  return (
    <section
      aria-labelledby={headingId}
      className="mb-8 rounded-2xl border border-line bg-surface p-6"
    >
      <div className="mb-5 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 id={headingId} className="text-lg font-semibold">
            {eventTitle(event)}
            <span className="font-normal text-muted"> · piscina de {event.pool_length_m} m</span>
          </h2>
          <p className="text-sm text-muted">
            {event.n_records} {event.n_records === 1 ? 'registro' : 'registros'} no período (
            {event.n_trainings} {event.n_trainings === 1 ? 'treino' : 'treinos'},{' '}
            {event.n_competitions}{' '}
            {event.n_competitions === 1 ? 'competição' : 'competições'}) · {event.n_history} no
            histórico
          </p>
        </div>
        <Link
          to={`/desempenho/${athleteId}?nado=${event.stroke}&prova=${event.distance_m}-${event.pool_length_m}`}
          className="inline-flex items-center gap-1 text-sm font-medium text-brand-text hover:underline"
        >
          Ver no Desempenho
          <ArrowRight size={14} aria-hidden="true" />
        </Link>
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <TimesCard event={event} />
        <PredictionCard
          event={event}
          minRecords={report.min_records}
          minTrendRecords={report.min_trend_records}
        />
      </div>

      <div className="mt-6">
        <h3 className="mb-2 text-sm font-semibold">Evolução do tempo</h3>
        <MetricChart
          data={chartData}
          metric={TIME_METRIC}
          lines={lines}
          futureFrom={futureFrom >= 0 ? futureFrom : null}
          format={formatTime}
        />
        <p className="mt-3 text-xs text-muted">
          {hasModel
            ? 'Pontos: registros do período. Linhas tracejadas: reta da Regressão Linear ajustada com todo o histórico da prova, prolongada para os próximos registros (sem data). Quanto mais distante, maior a incerteza.'
            : `Pontos: registros do período. A reta do modelo aparece a partir de ${report.min_records} registros desta prova.`}
        </p>
      </div>

      <div className="mt-6">
        <h3 className="mb-1 text-sm font-semibold">Métricas no período</h3>
        <MetricsTable event={event} minConclusive={report.min_conclusive_points} />
      </div>
    </section>
  )
}

export default function ReportPage() {
  const { athleteId } = useParams()
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const period = readPeriod(params)
  const key = JSON.stringify([athleteId, period])

  const [athletes, setAthletes] = useState({ loaded: false, items: [], error: '' })
  const [result, setResult] = useState({ key: null, data: null, error: '' })
  const loading = result.key !== key

  useEffect(() => {
    let cancelled = false
    listAthletes({ limit: 100 })
      .then((items) => {
        if (!cancelled) setAthletes({ loaded: true, items, error: '' })
      })
      .catch((err) => {
        if (!cancelled) setAthletes({ loaded: true, items: [], error: err.message })
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!athleteId) return undefined
    let cancelled = false
    const [id, days] = JSON.parse(key)
    getReport(id, { dateFrom: days ? isoDaysAgo(Number(days)) : '' })
      .then((data) => {
        if (!cancelled) setResult({ key, data, error: '' })
      })
      .catch((err) => {
        if (!cancelled) setResult({ key, data: null, error: err.message })
      })
    return () => {
      cancelled = true
    }
  }, [athleteId, key])

  function changePeriod(value) {
    const next = new URLSearchParams(params)
    if (value) next.set('periodo', value)
    else next.delete('periodo')
    setParams(next, { replace: true })
  }

  // Sem atleta na URL: abre o primeiro atleta ativo (ou o primeiro da lista)
  if (!athleteId) {
    if (!athletes.loaded) return <Spinner />
    if (athletes.error) return <Alert>{athletes.error}</Alert>
    const first = athletes.items.find((a) => a.active) ?? athletes.items[0]
    if (first) return <Navigate to={`/relatorios/${first.id}`} replace />
    return (
      <>
        <PageHeader title="Relatórios" description="Visão consolidada por atleta" />
        <div className="rounded-2xl border border-dashed border-line bg-surface py-16 text-center">
          <p className="font-medium">Nenhum atleta cadastrado</p>
          <p className="mt-1 text-sm text-muted">
            Cadastre um atleta e registre treinos para gerar o relatório.
          </p>
          <Link to="/atletas/novo" className={buttonClasses('primary', 'md', 'mt-6')}>
            Cadastrar atleta
          </Link>
        </div>
      </>
    )
  }

  const data = result.data
  const athleteOptions = athletes.items.map((a) => ({
    value: String(a.id),
    label: a.active ? a.name : `${a.name} (inativo)`,
  }))
  const athleteInList = athleteOptions.some((o) => o.value === athleteId)
  const search = period ? `?periodo=${period}` : ''

  return (
    <>
      <PageHeader
        title="Relatórios"
        description={
          data
            ? `Visão consolidada de ${data.athlete_name}${data.athlete_active ? '' : ' (inativo)'}`
            : 'Visão consolidada por atleta'
        }
      >
        <div className="flex flex-wrap items-center gap-2">
          {athletes.loaded && athleteInList && (
            <Select
              id="report-athlete"
              label="Atleta"
              options={athleteOptions}
              value={athleteId}
              onChange={(id) => navigate(`/relatorios/${id}${search}`)}
              className="w-64"
            />
          )}
          <Segmented
            options={PERIOD_OPTIONS}
            value={period}
            onChange={changePeriod}
            ariaLabel="Período do relatório"
          />
        </div>
      </PageHeader>

      {loading ? (
        <Spinner />
      ) : result.error ? (
        <div className="max-w-xl space-y-4">
          <Alert>{result.error}</Alert>
          <Link to="/relatorios" className={buttonClasses('secondary')}>
            Voltar
          </Link>
        </div>
      ) : (
        <>
          <section aria-labelledby="report-summary" className="mb-8">
            <h2 id="report-summary" className="sr-only">
              Resumo geral
            </h2>
            <div className="mb-4 rounded-2xl border border-line bg-surface p-5 text-sm">
              <p className="text-lg font-semibold">{data.athlete_name}</p>
              <p className="mt-1 text-muted">
                {calcAge(data.birth_date)} anos · {SEX_LABEL[data.sex]} ·{' '}
                {data.athlete_active ? 'Ativo' : 'Inativo'}
              </p>
              <p className="mt-1 text-muted">
                Período:{' '}
                {data.first_session_date
                  ? `${formatDate(data.first_session_date)} a ${formatDate(data.last_session_date)}`
                  : 'sem registros'}
                {period
                  ? ` (${PERIOD_OPTIONS.find((o) => o.value === period).label})`
                  : ' (todo o histórico)'}
              </p>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              <StatCard icon={Activity} label="Registros" value={data.totals.records} />
              <StatCard icon={Timer} label="Treinos" value={data.totals.trainings} />
              <StatCard icon={Medal} label="Competições" value={data.totals.competitions} />
              <StatCard icon={Layers} label="Provas" value={data.totals.events} />
            </div>
          </section>

          {data.events.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-line bg-surface py-16 text-center">
              <CalendarRange size={24} aria-hidden="true" className="mx-auto text-muted" />
              <p className="mt-3 font-medium">Nenhum registro de {data.athlete_name} no período</p>
              <p className="mt-1 text-sm text-muted">
                Escolha um período maior ou registre um treino.
              </p>
            </div>
          ) : (
            <>
              {data.events.map((event) => (
                <EventSection
                  key={`${event.stroke}-${event.distance_m}-${event.pool_length_m}`}
                  athleteId={athleteId}
                  event={event}
                  report={data}
                />
              ))}
              <p className="flex items-start gap-2 text-xs text-muted">
                <Info size={14} aria-hidden="true" className="mt-0.5 shrink-0" />
                O período filtra os registros, os tempos, as métricas e os pontos do gráfico. A
                previsão, o selo de tendência e a reta do modelo usam sempre todo o histórico de
                cada prova, como no Início e no Desempenho. O selo aparece a partir de{' '}
                {data.min_trend_records} registros na prova; a indicação de melhora ou piora das
                métricas, a partir de {data.min_conclusive_points} treinos no período.
              </p>
            </>
          )}
        </>
      )}
    </>
  )
}