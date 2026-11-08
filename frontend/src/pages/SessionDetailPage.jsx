import { ArrowLeft, ArrowRight, Pencil, Trash2 } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import MetricCard from '../components/MetricCard'
import MetricChart from '../components/MetricChart'
import MetricLegend from '../components/MetricLegend'
import PageHeader from '../components/PageHeader'
import Alert from '../components/ui/Alert'
import Button from '../components/ui/Button'
import { buttonClasses } from '../components/ui/button-styles'
import ChipGroup from '../components/ui/ChipGroup'
import Spinner from '../components/ui/Spinner'
import { getAthlete } from '../services/athletes'
import { deleteSession, getSession, listAthleteSessions } from '../services/sessions'
import { formatDate, formatShortDate } from '../utils/date'
import {
  METRICS,
  SESSION_TYPE_LABEL,
  STROKE_LABEL,
  formatDecimal,
  formatRace,
  formatTime,
} from '../utils/session'

const CHIP_OPTIONS = METRICS.map((m) => ({ value: m.key, label: m.short, title: m.label }))

function Info({ label, children, wide = false }) {
  return (
    <div className={wide ? 'sm:col-span-2' : ''}>
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="mt-1 text-sm font-medium">{children}</dd>
    </div>
  )
}

export default function SessionDetailPage() {
  const { athleteId, sessionId } = useParams()
  const navigate = useNavigate()
  const key = `${athleteId}/${sessionId}`
  const [state, setState] = useState({
    key: null,
    athlete: null,
    session: null,
    history: [],
    error: '',
  })
  const [metricKey, setMetricKey] = useState('vn')
  const [confirming, setConfirming] = useState(false)
  const [deleting, setDeleting] = useState(false)
  const [actionError, setActionError] = useState('')

  const loading = state.key !== key

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        const [athlete, session] = await Promise.all([
          getAthlete(athleteId),
          getSession(athleteId, sessionId),
        ])
        const history = await listAthleteSessions(athleteId, { stroke: session.stroke })
        if (!cancelled) setState({ key, athlete, session, history, error: '' })
      } catch (err) {
        if (!cancelled)
          setState({ key, athlete: null, session: null, history: [], error: err.message })
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [athleteId, sessionId, key])

  const metric = METRICS.find((m) => m.key === metricKey)

  const series = useMemo(
    () =>
      [...state.history].sort(
        (a, b) => a.session_date.localeCompare(b.session_date) || a.id - b.id,
      ),
    [state.history],
  )
  const chartData = useMemo(
    () =>
      series.map((s, index) => ({
        x: index,
        label: formatShortDate(s.session_date),
        value: s.metrics?.[metricKey] ?? null,
      })),
    [series, metricKey],
  )

  async function handleDelete() {
    setDeleting(true)
    setActionError('')
    try {
      await deleteSession(athleteId, sessionId)
      navigate('/treinos')
    } catch (err) {
      setActionError(err.message)
      setDeleting(false)
    }
  }

  if (loading) return <Spinner />
  if (state.error) {
    return (
      <div className="max-w-xl space-y-4">
        <Alert>{state.error}</Alert>
        <Link to="/treinos" className={buttonClasses('secondary')}>
          Voltar para treinos
        </Link>
      </div>
    )
  }

  const { athlete, session } = state
  const currentIndex = series.findIndex((s) => s.id === session.id)

  return (
    <>
      <Link
        to="/treinos"
        className="mb-6 inline-flex items-center gap-2 text-sm text-muted hover:text-fg"
      >
        <ArrowLeft size={16} aria-hidden="true" />
        Voltar para treinos
      </Link>

      <PageHeader
        title={athlete.name}
        description={`${formatRace(session)} · ${formatDate(session.session_date)} · ${
          SESSION_TYPE_LABEL[session.session_type]
        }`}
      >
        <div className="flex gap-2">
          <Link
            to={`/treinos/${athleteId}/${sessionId}/editar`}
            className={buttonClasses('secondary')}
          >
            <Pencil size={16} aria-hidden="true" />
            Editar
          </Link>
          <Button variant="danger" onClick={() => setConfirming(true)} disabled={confirming}>
            <Trash2 size={16} aria-hidden="true" />
            Excluir
          </Button>
        </div>
      </PageHeader>

      {confirming && (
        <div role="alert" className="mb-6 rounded-2xl border border-line bg-danger-soft p-5">
          <p className="font-medium text-danger">Excluir este treino?</p>
          <p className="mt-1 text-sm text-muted">
            O registro e suas métricas serão removidos do histórico do atleta. Essa ação não pode
            ser desfeita.
          </p>
          <div className="mt-4 flex gap-2">
            <Button variant="danger" onClick={handleDelete} disabled={deleting}>
              {deleting ? 'Excluindo…' : 'Sim, excluir'}
            </Button>
            <Button variant="secondary" onClick={() => setConfirming(false)} disabled={deleting}>
              Cancelar
            </Button>
          </div>
        </div>
      )}
      {actionError && (
        <div className="mb-6">
          <Alert>{actionError}</Alert>
        </div>
      )}

      <section aria-labelledby="metrics-title" className="mb-8">
        <h2 id="metrics-title" className="mb-4 text-lg font-semibold">
          Métricas
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {METRICS.map((m) => (
            <MetricCard key={m.key} metric={m} value={session.metrics?.[m.key]} />
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
              Evolução
            </h2>
            <p className="text-sm text-muted">
              {metric.label} nos treinos de {STROKE_LABEL[session.stroke]} de {athlete.name}
            </p>
          </div>
          <ChipGroup
            options={CHIP_OPTIONS}
            value={metricKey}
            onChange={setMetricKey}
            ariaLabel="Métrica exibida no gráfico"
          />
        </div>
        <MetricChart data={chartData} metric={metric} currentIndex={currentIndex} />
        <div className="mt-3 flex flex-wrap items-center justify-between gap-2">
          <p className="text-xs text-muted">
            {series.length < 2
              ? `Registre mais treinos de ${STROKE_LABEL[session.stroke]} para acompanhar a evolução.`
              : 'O ponto com contorno destacado é o treino exibido nesta página.'}
          </p>
          <Link
            to={`/desempenho/${athleteId}?nado=${session.stroke}&prova=${session.distance_m}-${session.pool_length_m}`}
            className="inline-flex items-center gap-1 text-sm font-medium text-brand-text hover:underline"
          >
            Ver desempenho completo
            <ArrowRight size={14} aria-hidden="true" />
          </Link>
        </div>
        <MetricLegend metric={metric} />
      </section>

      <section
        aria-labelledby="data-title"
        className="rounded-2xl border border-line bg-surface p-6"
      >
        <h2 id="data-title" className="mb-4 text-lg font-semibold">
          Dados do registro
        </h2>
        <dl className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          <Info label="Tipo">{SESSION_TYPE_LABEL[session.session_type]}</Info>
          <Info label="Data">{formatDate(session.session_date)}</Info>
          <Info label="Nado">{STROKE_LABEL[session.stroke]}</Info>
          <Info label="Piscina">{session.pool_length_m} m</Info>
          <Info label="Distância total">{session.distance_m} m</Info>
          <Info label="Tempo total">{formatTime(session.total_time_s)}</Info>
          <Info label="Trecho de nado puro">
            {formatDecimal(session.swim_distance_m)} m em {formatTime(session.swim_time_s)}
          </Info>
          <Info label="Ciclos no trecho de nado puro">{session.stroke_count}</Info>
          <Info label="Ciclos na prova completa">
            {session.total_cycle_count ?? (
              <span className="font-normal text-muted">
                Não informado (edite o treino para calcular o SWOLF)
              </span>
            )}
          </Info>
          <Info label="Observações" wide>
            {session.notes || <span className="font-normal text-muted">Sem observações</span>}
          </Info>
        </dl>
      </section>
    </>
  )
}