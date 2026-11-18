import { ArrowRight, Info, Plus, Sparkles } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import MetricChart from '../components/MetricChart'
import MetricLegend from '../components/MetricLegend'
import MetricTrendCard from '../components/MetricTrendCard'
import PageHeader from '../components/PageHeader'
import PredictionPanel from '../components/PredictionPanel'
import Alert from '../components/ui/Alert'
import { buttonClasses } from '../components/ui/button-styles'
import ChipGroup from '../components/ui/ChipGroup'
import Dash from '../components/ui/Dash'
import Segmented from '../components/ui/Segmented'
import Select from '../components/ui/Select'
import Spinner from '../components/ui/Spinner'
import { listAthletes } from '../services/athletes'
import { getPerformance } from '../services/performance'
import { getPrediction } from '../services/prediction'
import { formatDate, formatShortDate, isoDaysAgo } from '../utils/date'
import {
  METRICS,
  SESSION_TYPE_LABEL,
  TIME_METRIC,
  STROKE_LABEL,
  formatDecimal,
  formatRace,
  formatTime,
} from '../utils/session'

const STROKE_ORDER = ['freestyle', 'backstroke', 'breaststroke', 'butterfly', 'medley']

const TYPE_OPTIONS = [
  { value: '', label: 'Todos' },
  { value: 'training', label: 'Treinos' },
  { value: 'competition', label: 'Competições' },
]

const PERIOD_OPTIONS = [
  { value: '30', label: '30 dias' },
  { value: '90', label: '90 dias' },
  { value: '365', label: '12 meses' },
  { value: '', label: 'Tudo' },
]

const RECENT_ROWS = 10

// opções do gráfico: o tempo da prova (com a previsão) e as métricas calculadas
const CHART_OPTIONS = [TIME_METRIC, ...METRICS].map((m) => ({
  value: m.key,
  label: m.short,
  title: m.label,
}))

const PREDICTION_LINES = {
  training: { dataKey: 'model', name: 'Previsão para treino', color: 'var(--accent)', dashed: true },
  competition: {
    dataKey: 'modelComp',
    name: 'Previsão para competição',
    color: 'var(--warning)',
    dashed: true,
  },
}

// Lê os filtros da URL e descarta valores inválidos (link editado à mão, por exemplo)
function readFilters(params) {
  const stroke = params.get('nado') ?? ''
  const event = params.get('prova') ?? ''
  const type = params.get('tipo') ?? ''
  const period = params.get('periodo') ?? ''
  return {
    stroke: STROKE_ORDER.includes(stroke) ? stroke : '',
    event: /^\d+-(25|50)$/.test(event) ? event : '',
    type: TYPE_OPTIONS.some((o) => o.value === type) ? type : '',
    period: PERIOD_OPTIONS.some((o) => o.value === period) ? period : '',
  }
}

const eventKey = (e) => `${e.distance_m}-${e.pool_length_m}`
const eventLabel = (e) => `${e.distance_m} m · piscina de ${e.pool_length_m} m`

export default function PerformancePage() {
  const { athleteId } = useParams()
  const navigate = useNavigate()
  const [params, setParams] = useSearchParams()
  const filters = readFilters(params)
  const key = JSON.stringify([athleteId, filters])

  const [athletes, setAthletes] = useState({ loaded: false, items: [], error: '' })
  const [result, setResult] = useState({ key: null, data: null, error: '' })
  const [prediction, setPrediction] = useState({ key: null, data: null, error: '' })
  const [metricKey, setMetricKey] = useState(TIME_METRIC.key)

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
    const { stroke, event, type, period } = JSON.parse(key)[1]
    const [distance, pool] = event ? event.split('-') : []
    getPerformance(athleteId, {
      stroke,
      distance,
      pool,
      sessionType: type,
      dateFrom: period ? isoDaysAgo(Number(period)) : '',
    })
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

  const data = result.data
  const isTime = metricKey === TIME_METRIC.key
  const metric = isTime ? TIME_METRIC : METRICS.find((m) => m.key === metricKey)

  const strokeOptions = useMemo(() => {
    if (!data) return []
    const totals = {}
    for (const e of data.events) totals[e.stroke] = (totals[e.stroke] ?? 0) + e.sessions
    return STROKE_ORDER.filter((s) => totals[s]).map((s) => ({
      value: s,
      label: `${STROKE_LABEL[s]} (${totals[s]})`,
    }))
  }, [data])

  const strokeEvents = useMemo(
    () => (data ? data.events.filter((e) => e.stroke === data.stroke) : []),
    [data],
  )

  const eventOptions = useMemo(
    () => [
      { value: '', label: 'Todas as distâncias' },
      ...strokeEvents.map((e) => ({
        value: eventKey(e),
        label: `${eventLabel(e)} (${e.sessions})`,
      })),
    ],
    [strokeEvents],
  )

  const selectedEvent = strokeEvents.find((e) => eventKey(e) === filters.event)
  // a previsão precisa de uma prova só: a escolhida ou, se o nado tiver uma única, essa
  const predictionEvent = selectedEvent ?? (strokeEvents.length === 1 ? strokeEvents[0] : null)
  const predictionKey =
    data && predictionEvent
      ? [athleteId, data.stroke, predictionEvent.distance_m, predictionEvent.pool_length_m].join('|')
      : null

  useEffect(() => {
    if (!predictionKey) return undefined
    let cancelled = false
    const [id, stroke, distance, pool] = predictionKey.split('|')
    getPrediction(id, { stroke, distance, pool })
      .then((value) => {
        if (!cancelled) setPrediction({ key: predictionKey, data: value, error: '' })
      })
      .catch((err) => {
        if (!cancelled) setPrediction({ key: predictionKey, data: null, error: err.message })
      })
    return () => {
      cancelled = true
    }
  }, [predictionKey])

  const predictionLoading = predictionKey != null && prediction.key !== predictionKey
  const predictionData = !predictionLoading && predictionKey ? prediction.data : null
  const metricSeries = isTime ? null : (predictionData?.metric_series?.[metricKey] ?? null)

  // Com previsão disponível (tempo ou métrica), o gráfico usa todo o histórico da prova e a
  // reta do modelo; sem ela, volta aos registros filtrados (com a linha de tendência).
  const forecast = useMemo(() => {
    const history = predictionData?.history ?? []
    if (!history.length) return null
    if (isTime) {
      if (!predictionData.path?.length) return null
      return { history, values: history.map((h) => h.time_s), path: predictionData.path }
    }
    if (!metricSeries?.path?.length) return null
    return { history, values: metricSeries.values, path: metricSeries.path }
  }, [predictionData, isTime, metricSeries])

  const chartData = useMemo(() => {
    if (forecast) {
      const { history, values, path } = forecast
      const past = history.map((h, i) => ({
        x: i,
        label: formatShortDate(h.session_date),
        detail: SESSION_TYPE_LABEL[h.session_type],
        value: values[i] ?? null,
        isCompetition: h.session_type === 'competition',
        model: path[i]?.training_s ?? null,
        modelComp: path[i]?.competition_s ?? null,
      }))
      const future = path.slice(history.length).map((p, k) => ({
        x: history.length + k,
        label: `Próx. ${k + 1}`,
        detail: `Previsão do ${history.length + k + 1}º registro`,
        value: null,
        model: p.training_s,
        modelComp: p.competition_s,
      }))
      return [...past, ...future]
    }
    return (data?.sessions ?? []).map((s, index) => ({
      x: index,
      label: formatShortDate(s.session_date),
      detail: `${formatRace(s)} · piscina de ${s.pool_length_m} m · ${
        SESSION_TYPE_LABEL[s.session_type]
      }`,
      value: isTime ? s.total_time_s : (s.metrics?.[metricKey] ?? null),
      isCompetition: isTime && s.session_type === 'competition',
    }))
  }, [data, metricKey, isTime, forecast])

  const chartLines = useMemo(() => {
    if (!forecast) return []
    const lines = [PREDICTION_LINES.training]
    if (forecast.path.some((p) => p.competition_s != null)) lines.push(PREDICTION_LINES.competition)
    return lines
  }, [forecast])

  const futureSteps = forecast ? forecast.path.length - forecast.history.length : 0
  const minRecords = predictionData?.min_records ?? 6

  const summary = data?.summary?.[metricKey] ?? null

  // texto explicativo abaixo do gráfico
  let chartNote
  if (forecast) {
    chartNote = `Linhas tracejadas: reta da Regressão Linear (todo o histórico da prova), prolongada para os próximos ${futureSteps} registros na área "Previsão" (sem data: o modelo usa a ordem dos registros). Quanto mais distante, maior a incerteza.`
  } else {
    const parts = []
    if (!predictionKey) {
      parts.push('Escolha uma prova no filtro acima para ver a previsão no gráfico.')
    } else if (predictionLoading) {
      parts.push('Carregando a previsão…')
    } else if (metricSeries && !metricSeries.available) {
      parts.push(
        `A previsão de ${metric.short} aparece a partir de ${minRecords} registros desta prova com o valor calculado (há ${metricSeries.n_records}).`,
      )
    } else if (predictionData) {
      parts.push(`A previsão aparece a partir de ${minRecords} registros desta prova.`)
    }
    if (!isTime) {
      parts.push(
        summary?.trend
          ? 'Linha tracejada: tendência do período (regressão linear pelos mínimos quadrados).'
          : 'A linha de tendência aparece a partir de 3 treinos com esses filtros.',
      )
    }
    if (data?.truncated) {
      parts.push(`Exibindo os ${data.sessions.length} treinos mais recentes de ${data.total}.`)
    }
    chartNote = parts.join(' ')
  }

  const recent = useMemo(
    () => [...(data?.sessions ?? [])].reverse().slice(0, RECENT_ROWS),
    [data],
  )

  function updateFilters(changes) {
    const names = { stroke: 'nado', event: 'prova', type: 'tipo', period: 'periodo' }
    const next = new URLSearchParams(params)
    for (const [field, value] of Object.entries(changes)) {
      if (value) next.set(names[field], value)
      else next.delete(names[field])
    }
    setParams(next, { replace: true })
  }

  // Sem atleta na URL: abre o primeiro atleta ativo (ou o primeiro da lista)
  if (!athleteId) {
    if (!athletes.loaded) return <Spinner />
    if (athletes.error) return <Alert>{athletes.error}</Alert>
    const first = athletes.items.find((a) => a.active) ?? athletes.items[0]
    if (first) return <Navigate to={`/desempenho/${first.id}`} replace />
    return (
      <>
        <PageHeader title="Desempenho" description="Evolução das métricas por atleta" />
        <div className="rounded-2xl border border-dashed border-line bg-surface py-16 text-center">
          <p className="font-medium">Nenhum atleta cadastrado</p>
          <p className="mt-1 text-sm text-muted">
            Cadastre um atleta e registre treinos para acompanhar a evolução.
          </p>
          <Link to="/atletas/novo" className={buttonClasses('primary', 'md', 'mt-6')}>
            Cadastrar atleta
          </Link>
        </div>
      </>
    )
  }

  const athleteOptions = athletes.items.map((a) => ({
    value: String(a.id),
    label: a.active ? a.name : `${a.name} (inativo)`,
  }))
  const athleteInList = athleteOptions.some((o) => o.value === athleteId)

  const mixedDistances = data && !filters.event && strokeEvents.length > 1

  return (
    <>
      <PageHeader
        title="Desempenho"
        description={
          data
            ? `Evolução das métricas de ${data.athlete_name}${
                data.athlete_active ? '' : ' (inativo)'
              }`
            : 'Evolução das métricas por atleta'
        }
      >
        <div className="flex flex-wrap items-center gap-2">
          {athletes.loaded && athleteInList && (
            <Select
              id="athlete"
              label="Atleta"
              options={athleteOptions}
              value={athleteId}
              onChange={(id) => navigate(`/desempenho/${id}`)}
              className="w-64"
            />
          )}
          {data?.athlete_active && (
            <Link to="/treinos/novo" className={buttonClasses('primary')}>
              <Plus size={16} aria-hidden="true" />
              Novo treino
            </Link>
          )}
        </div>
      </PageHeader>

      {loading ? (
        <Spinner />
      ) : result.error ? (
        <div className="max-w-xl space-y-4">
          <Alert>{result.error}</Alert>
          <Link to="/desempenho" className={buttonClasses('secondary')}>
            Voltar
          </Link>
        </div>
      ) : data.events.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-line bg-surface py-16 text-center">
          <p className="font-medium">Nenhum treino registrado para {data.athlete_name}</p>
          <p className="mt-1 text-sm text-muted">
            A evolução aparece a partir do segundo treino do mesmo nado.
          </p>
          {data.athlete_active && (
            <Link to="/treinos/novo" className={buttonClasses('primary', 'md', 'mt-6')}>
              Registrar treino
            </Link>
          )}
        </div>
      ) : (
        <>
          <section
            aria-label="Filtros"
            className="mb-8 space-y-4 rounded-2xl border border-line bg-surface p-5"
          >
            <ChipGroup
              options={strokeOptions}
              value={data.stroke}
              onChange={(stroke) => updateFilters({ stroke, event: '' })}
              ariaLabel="Nado"
            />
            <div className="flex flex-wrap items-center gap-3">
              <Select
                id="event"
                label="Prova"
                options={eventOptions}
                value={filters.event}
                onChange={(event) => updateFilters({ event })}
                className="w-full sm:w-72"
              />
              <Segmented
                options={TYPE_OPTIONS}
                value={filters.type}
                onChange={(type) => updateFilters({ type })}
                ariaLabel="Tipo de registro"
              />
              <Segmented
                options={PERIOD_OPTIONS}
                value={filters.period}
                onChange={(period) => updateFilters({ period })}
                ariaLabel="Período"
              />
            </div>
            {mixedDistances && (
              <p className="flex items-start gap-2 text-sm text-muted">
                <Info size={16} aria-hidden="true" className="mt-0.5 shrink-0" />
                Distâncias e piscinas diferentes estão misturadas. Para comparar de forma justa,
                escolha uma prova.
              </p>
            )}
          </section>

          {data.sessions.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-line bg-surface py-16 text-center">
              <p className="font-medium">Nenhum treino com esses filtros</p>
              <p className="mt-1 text-sm text-muted">Amplie o período ou escolha outra prova.</p>
            </div>
          ) : (
            <>
              <section aria-labelledby="summary-title" className="mb-8">
                <h2 id="summary-title" className="mb-1 text-lg font-semibold">
                  Resumo do período
                </h2>
                <p className="mb-4 text-sm text-muted">
                  Valor do treino mais recente e tendência do período (regressão linear sobre
                  os treinos). A reta aparece a partir de 3 treinos; a indicação de melhora ou
                  piora, a partir de {data.min_conclusive_points}. Clique em uma métrica para
                  vê-la no gráfico.
                </p>
                <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                  {METRICS.map((m) => (
                    <MetricTrendCard
                      key={m.key}
                      metric={m}
                      summary={data.summary[m.key]}
                      minConclusive={data.min_conclusive_points}
                      selected={m.key === metricKey}
                      onSelect={() => setMetricKey(m.key)}
                    />
                  ))}
                </div>
              </section>

              <section
                aria-labelledby="chart-title"
                className="mb-8 rounded-2xl border border-line bg-surface p-6"
              >
                <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <h2 id="chart-title" className="text-lg font-semibold">
                      Evolução: {metric.label}
                    </h2>
                    <p className="text-sm text-muted">
                      {forecast
                        ? `${forecast.history.length} registros de ${STROKE_LABEL[data.stroke]} · ${eventLabel(
                            predictionEvent,
                          )} (todo o histórico da prova)`
                        : `${data.sessions.length} ${
                            data.sessions.length === 1 ? 'treino' : 'treinos'
                          } de ${STROKE_LABEL[data.stroke]}${
                            selectedEvent ? ` · ${eventLabel(selectedEvent)}` : ''
                          }`}
                    </p>
                  </div>
                  <ChipGroup
                    options={CHART_OPTIONS}
                    value={metricKey}
                    onChange={setMetricKey}
                    ariaLabel="Métrica exibida no gráfico"
                  />
                </div>
                <MetricChart
                  data={chartData}
                  metric={metric}
                  trend={forecast || isTime ? null : (summary?.trend ?? null)}
                  lines={chartLines}
                  futureFrom={forecast ? forecast.history.length : null}
                  format={isTime ? formatTime : null}
                />
                <p className="mt-3 text-xs text-muted">{chartNote}</p>
                <MetricLegend metric={metric} />
              </section>

              {predictionEvent ? (
                <PredictionPanel
                  loading={predictionLoading}
                  error={prediction.key === predictionKey ? prediction.error : ''}
                  data={predictionData}
                />
              ) : (
                <p className="mb-8 flex items-start gap-2 rounded-2xl border border-dashed border-line bg-surface px-5 py-4 text-sm text-muted">
                  <Sparkles size={16} aria-hidden="true" className="mt-0.5 shrink-0" />
                  Escolha uma prova no filtro acima para ver a previsão de tempo do próximo
                  registro.
                </p>
              )}

              <section
                aria-labelledby="recent-title"
                className="overflow-hidden rounded-2xl border border-line bg-surface"
              >
                <div className="flex flex-wrap items-center justify-between gap-2 p-6 pb-4">
                  <h2 id="recent-title" className="text-lg font-semibold">
                    Treinos do período
                  </h2>
                  {data.sessions.length > RECENT_ROWS && (
                    <p className="text-sm text-muted">
                      Mostrando os {RECENT_ROWS} mais recentes de {data.sessions.length}
                    </p>
                  )}
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[48rem] text-left text-sm">
                    <thead className="bg-subtle text-xs uppercase tracking-wide text-muted">
                      <tr>
                        <th scope="col" className="px-5 py-3 font-medium">Data</th>
                        <th scope="col" className="px-5 py-3 font-medium">Prova</th>
                        <th scope="col" className="px-5 py-3 font-medium">Tipo</th>
                        <th scope="col" className="px-5 py-3 font-medium">Tempo</th>
                        {!isTime && (
                          <th scope="col" className="px-5 py-3 font-medium">{metric.short}</th>
                        )}
                        <th scope="col" className="px-5 py-3">
                          <span className="sr-only">Ações</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {recent.map((s) => {
                        const value = s.metrics?.[metricKey]
                        return (
                          <tr key={s.id} className="border-t border-line">
                            <td className="px-5 py-4 text-muted">{formatDate(s.session_date)}</td>
                            <td className="px-5 py-4">
                              {formatRace(s)}
                              <span className="text-muted"> · {s.pool_length_m} m</span>
                            </td>
                            <td className="px-5 py-4">{SESSION_TYPE_LABEL[s.session_type]}</td>
                            <td className="px-5 py-4 font-semibold">{formatTime(s.total_time_s)}</td>
                            {!isTime && (
                              <td className="px-5 py-4">
                                {value != null ? (
                                  `${formatDecimal(value, metric.digits)}${
                                    metric.unit ? ` ${metric.unit}` : ''
                                  }`
                                ) : (
                                  <Dash />
                                )}
                              </td>
                            )}
                            <td className="px-5 py-4 text-right">
                              <Link
                                to={`/treinos/${s.athlete_id}/${s.id}`}
                                className="inline-flex items-center gap-1 font-medium text-brand-text hover:underline"
                              >
                                Ver detalhes
                                <ArrowRight size={14} aria-hidden="true" />
                                <span className="sr-only"> do treino de {formatDate(s.session_date)}</span>
                              </Link>
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
              </section>
            </>
          )}
        </>
      )}
    </>
  )
}