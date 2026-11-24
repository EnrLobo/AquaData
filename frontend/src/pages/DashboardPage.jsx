import { Activity, ArrowRight, Info, Plus, Timer, UserX, Users } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Alert from '../components/ui/Alert'
import Badge from '../components/ui/Badge'
import { buttonClasses } from '../components/ui/button-styles'
import Select from '../components/ui/Select'
import Spinner from '../components/ui/Spinner'
import { useAuth } from '../hooks/useAuth'
import { getDashboard } from '../services/dashboard'
import { formatDate } from '../utils/date'
import { STROKE_LABEL, formatDecimal, formatRace, formatTime } from '../utils/session'
import { initials } from '../utils/text'

function Panel({ title, action, children, className = '' }) {
  return (
    <section className={`rounded-2xl border border-line bg-surface ${className}`}>
      <header className="flex items-center justify-between border-b border-line px-5 py-4">
        <h2 className="text-base font-semibold">{title}</h2>
        {action}
      </header>
      {children}
    </section>
  )
}

function SeeAll({ to, children }) {
  return (
    <Link
      to={to}
      className="inline-flex items-center gap-1 text-sm font-medium text-brand-text hover:underline"
    >
      {children}
      <ArrowRight size={14} aria-hidden="true" />
    </Link>
  )
}

// selo da tendência prevista (inclinação da reta do tempo; menor tempo = melhor)
const STATUS = {
  improving: { label: 'Melhorando', tone: 'success' },
  stable: { label: 'Estável', tone: 'neutral' },
  attention: { label: 'Atenção', tone: 'warning' },
}

const STROKE_ORDER = ['freestyle', 'backstroke', 'breaststroke', 'butterfly', 'medley']
const MAIN_EVENT = '' // opção padrão: a prova principal de cada atleta
const VISIBLE_ROWS = 10

const eventKey = (p) => `${p.stroke}-${p.distance_m}-${p.pool_length_m}`

function signed(value, digits = 2) {
  const sign = value > 0 ? '+' : value < 0 ? '−' : ''
  return `${sign}${formatDecimal(Math.abs(value), digits)}`
}

function PredictionsPanel({ predictions, withoutPrediction, minTrendRecords }) {
  const [event, setEvent] = useState(MAIN_EVENT)
  const [showAll, setShowAll] = useState(false)

  // provas com previsão para algum atleta, com a quantidade de atletas em cada uma
  const eventOptions = useMemo(() => {
    const events = new Map()
    for (const p of predictions) {
      const key = eventKey(p)
      const current = events.get(key)
      events.set(key, { ...p, athletes: (current?.athletes ?? 0) + 1 })
    }
    const sorted = [...events.entries()].sort(
      ([, a], [, b]) =>
        STROKE_ORDER.indexOf(a.stroke) - STROKE_ORDER.indexOf(b.stroke) ||
        a.distance_m - b.distance_m ||
        a.pool_length_m - b.pool_length_m,
    )
    return [
      { value: MAIN_EVENT, label: 'Prova principal de cada atleta' },
      ...sorted.map(([key, e]) => ({
        value: key,
        label: `${e.distance_m} m ${STROKE_LABEL[e.stroke]} · piscina de ${e.pool_length_m} m (${
          e.athletes
        } ${e.athletes === 1 ? 'atleta' : 'atletas'})`,
      })),
    ]
  }, [predictions])

  // a prova escolhida pode sumir (ex.: atleta inativado); nesse caso volta ao padrão
  const selected = eventOptions.some((o) => o.value === event) ? event : MAIN_EVENT
  const filtered = predictions.filter((p) =>
    selected === MAIN_EVENT ? p.is_main : eventKey(p) === selected,
  )
  const items = showAll ? filtered : filtered.slice(0, VISIBLE_ROWS)

  return (
    <Panel
      title="Previsões"
      className="mt-8"
      action={<SeeAll to="/desempenho">Ver desempenho</SeeAll>}
    >
      <div className="flex flex-wrap items-end justify-between gap-3 px-5 pt-4">
        <p className="max-w-2xl text-sm text-muted">
          Próximo tempo previsto para cada atleta, a partir do histórico da prova.
        </p>
        {predictions.length > 0 && (
          <Select
            id="prediction-event"
            label="Prova"
            options={eventOptions}
            value={selected}
            onChange={(value) => {
              setEvent(value)
              setShowAll(false)
            }}
            className="w-full sm:w-80"
          />
        )}
      </div>
      {items.length === 0 ? (
        <p className="m-5 flex items-start gap-2 rounded-xl bg-subtle px-4 py-3 text-sm text-muted">
          <Info size={16} aria-hidden="true" className="mt-0.5 shrink-0" />
          Nenhum atleta ativo tem 6 registros na mesma prova ainda. A previsão aparece a partir
          daí.
        </p>
      ) : (
        <>
          {/* celular e tablet em pé: cartões; telas largas: tabela (AQ-26) */}
          <ul className="my-4 grid grid-cols-1 gap-3 px-5 md:grid-cols-2 lg:hidden">
            {items.map((p) => {
              const status = p.status ? STATUS[p.status] : null
              return (
                <li
                  key={`${p.athlete_id}-${eventKey(p)}`}
                  className="rounded-xl border border-line bg-canvas p-4"
                >
                  <div className="flex items-start gap-3">
                    <span
                      aria-hidden="true"
                      className="grid size-8 shrink-0 place-items-center rounded-full bg-brand-soft text-xs font-semibold text-brand-text"
                    >
                      {initials(p.athlete_name)}
                    </span>
                    <div className="min-w-0 flex-1">
                      <p className="truncate font-medium">{p.athlete_name}</p>
                      <p className="text-xs text-muted">
                        {formatRace(p)} · piscina de {p.pool_length_m} m
                      </p>
                    </div>
                    {status ? (
                      <Badge tone={status.tone}>{status.label}</Badge>
                    ) : (
                      <Badge tone="neutral">
                        {p.n_records} de {minTrendRecords}
                      </Badge>
                    )}
                  </div>
                  <dl className="mt-3 grid grid-cols-3 gap-2 text-sm">
                    <div>
                      <dt className="text-xs text-muted">Último</dt>
                      <dd className="font-medium">{formatTime(p.last_time_s)}</dd>
                    </div>
                    <div>
                      <dt className="text-xs text-muted">Próx. treino</dt>
                      <dd className="font-semibold">
                        {p.training_s != null ? formatTime(p.training_s) : '—'}
                      </dd>
                    </div>
                    <div>
                      <dt className="text-xs text-muted">Próx. competição</dt>
                      <dd className="font-semibold">
                        {p.competition_s != null ? formatTime(p.competition_s) : '—'}
                      </dd>
                    </div>
                  </dl>
                  <div className="mt-3 flex items-center justify-between gap-2 text-xs text-muted">
                    <span>
                      {status ? '' : 'Poucos registros · '}
                      {signed(p.coef_order)} s por registro
                    </span>
                    <Link
                      to={`/desempenho/${p.athlete_id}?nado=${p.stroke}&prova=${p.distance_m}-${p.pool_length_m}`}
                      className="inline-flex min-h-10 items-center gap-1 text-sm font-medium text-brand-text hover:underline"
                    >
                      Ver gráfico
                      <ArrowRight size={14} aria-hidden="true" />
                      <span className="sr-only"> de {p.athlete_name}</span>
                    </Link>
                  </div>
                </li>
              )
            })}
          </ul>
          <div className="mt-3 hidden overflow-x-auto lg:block">
            <table className="w-full min-w-[52rem] text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-muted">
                <tr>
                  <th scope="col" className="px-5 py-3 font-medium">Atleta</th>
                  <th scope="col" className="px-5 py-3 font-medium">Prova</th>
                  <th scope="col" className="px-5 py-3 font-medium">Último</th>
                  <th scope="col" className="px-5 py-3 font-medium">Próximo treino</th>
                  <th scope="col" className="px-5 py-3 font-medium">Próxima competição</th>
                  <th scope="col" className="px-5 py-3 font-medium">Tendência</th>
                  <th scope="col" className="px-5 py-3">
                    <span className="sr-only">Ações</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {items.map((p) => {
                  const status = p.status ? STATUS[p.status] : null
                  return (
                    <tr key={`${p.athlete_id}-${eventKey(p)}`} className="border-t border-line">
                      <td className="px-5 py-3">
                        <div className="flex items-center gap-3">
                          <span
                            aria-hidden="true"
                            className="grid size-8 shrink-0 place-items-center rounded-full bg-brand-soft text-xs font-semibold text-brand-text"
                          >
                            {initials(p.athlete_name)}
                          </span>
                          <span className="font-medium">{p.athlete_name}</span>
                        </div>
                      </td>
                      <td className="px-5 py-3">
                        {formatRace(p)}
                        <span className="text-muted"> · {p.pool_length_m} m</span>
                      </td>
                      <td className="px-5 py-3">
                        {formatTime(p.last_time_s)}
                        <span className="block text-xs text-muted">
                          {formatDate(p.last_session_date)}
                        </span>
                      </td>
                      <td className="px-5 py-3 font-semibold">
                        {p.training_s != null ? formatTime(p.training_s) : '—'}
                      </td>
                      <td className="px-5 py-3 font-semibold">
                        {p.competition_s != null ? formatTime(p.competition_s) : '—'}
                      </td>
                      <td className="px-5 py-3">
                        {status ? (
                          <Badge tone={status.tone}>{status.label}</Badge>
                        ) : (
                          <Badge tone="neutral">
                            Poucos registros ({p.n_records} de {minTrendRecords})
                          </Badge>
                        )}
                        <span className="mt-1 block text-xs text-muted">
                          {signed(p.coef_order)} s por registro
                        </span>
                      </td>
                      <td className="px-5 py-3 text-right">
                        <Link
                          to={`/desempenho/${p.athlete_id}?nado=${p.stroke}&prova=${p.distance_m}-${p.pool_length_m}`}
                          className="inline-flex items-center gap-1 font-medium text-brand-text hover:underline"
                        >
                          Ver gráfico
                          <ArrowRight size={14} aria-hidden="true" />
                          <span className="sr-only"> de {p.athlete_name}</span>
                        </Link>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </>
      )}
      {filtered.length > VISIBLE_ROWS && (
        <div className="border-t border-line px-5 py-3 text-xs text-muted">
          {`Mostrando ${items.length} de ${filtered.length} atletas. `}
          <button
            type="button"
            onClick={() => setShowAll((value) => !value)}
            className="font-medium text-brand-text hover:underline"
          >
            {showAll ? 'Mostrar menos' : 'Mostrar todos'}
          </button>
        </div>
      )}
      <details className="group border-t border-line px-5 py-3 text-xs text-muted">
        <summary className="flex cursor-pointer list-none items-center gap-1.5 font-medium text-brand-text hover:underline">
          <Info size={14} aria-hidden="true" />
          Como ler esta tabela
        </summary>
        <ul className="mt-2 list-disc space-y-1 pl-5">
          <li>
            Por padrão, aparece a prova principal de cada atleta (a que tem mais registros). Use o
            seletor para ver outra prova.
          </li>
          <li>
            A tendência indica se o tempo vem caindo (Melhorando), subindo (Atenção) ou quase
            parado (Estável: variação menor que 0,2% do último tempo a cada registro).
          </li>
          <li>
            O selo aparece a partir de {minTrendRecords} registros na prova; com menos, o
            resultado ainda muda muito de um registro para outro. Quem precisa de atenção aparece
            primeiro.
          </li>
          {withoutPrediction > 0 && (
            <li>
              {withoutPrediction}{' '}
              {withoutPrediction === 1
                ? 'atleta ativo ainda não tem'
                : 'atletas ativos ainda não têm'}{' '}
              6 registros na mesma prova, o mínimo para a previsão.
            </li>
          )}
        </ul>
      </details>
    </Panel>
  )
}

export default function DashboardPage() {
  const { coach } = useAuth()
  const [state, setState] = useState({ loaded: false, data: null, error: '' })

  useEffect(() => {
    let cancelled = false
    getDashboard()
      .then((data) => {
        if (!cancelled) setState({ loaded: true, data, error: '' })
      })
      .catch((err) => {
        if (!cancelled) setState({ loaded: true, data: null, error: err.message })
      })
    return () => {
      cancelled = true
    }
  }, [])

  const firstName = coach.name.split(' ')[0]
  const { loaded, data, error } = state

  return (
    <>
      <PageHeader
        title={`Olá, ${firstName}`}
        description="Resumo dos seus atletas e das previsões de tempo."
      >
        <div className="flex flex-wrap gap-2">
          <Link to="/atletas/novo" className={buttonClasses('secondary')}>
            Novo atleta
          </Link>
          <Link to="/treinos/novo" className={buttonClasses('primary')}>
            <Plus size={16} aria-hidden="true" />
            Novo treino
          </Link>
        </div>
      </PageHeader>

      {!loaded ? (
        <Spinner />
      ) : error ? (
        <Alert>{error}</Alert>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <StatCard
              icon={Users}
              label="Atletas ativos"
              value={data.active_athletes}
              hint="sob sua orientação"
            />
            <StatCard
              icon={Timer}
              label="Treinos nos últimos 30 dias"
              value={data.sessions_last_30_days}
            />
            <StatCard
              icon={UserX}
              label="Sem treino há 30 dias"
              value={data.athletes_without_recent_sessions}
              hint="atletas ativos"
              tone={data.athletes_without_recent_sessions > 0 ? 'warning' : 'default'}
            />
            <StatCard
              icon={Activity}
              label="Treinos registrados"
              value={data.sessions_total}
              hint="no total"
            />
          </div>

          <PredictionsPanel
            predictions={data.predictions}
            withoutPrediction={data.athletes_without_prediction}
            minTrendRecords={data.min_trend_records}
          />
        </>
      )}
    </>
  )
}