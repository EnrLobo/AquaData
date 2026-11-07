import { Activity, ArrowRight, Plus, Timer, UserX, Users } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import Alert from '../components/ui/Alert'
import { buttonClasses } from '../components/ui/button-styles'
import Spinner from '../components/ui/Spinner'
import { useAuth } from '../hooks/useAuth'
import { getDashboard } from '../services/dashboard'
import { formatDate, formatDaysAgo } from '../utils/date'
import { formatRace, formatTime } from '../utils/session'
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

function Empty({ title, text, to, cta }) {
  return (
    <div className="px-5 py-10 text-center">
      <p className="font-medium">{title}</p>
      <p className="mt-1 text-sm text-muted">{text}</p>
      <Link to={to} className={buttonClasses('primary', 'md', 'mt-5')}>
        {cta}
      </Link>
    </div>
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
        description="Visão geral dos seus atletas e dos últimos treinos."
      >
        <div className="flex gap-2">
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
          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
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

          <div className="mt-8 grid gap-6 lg:grid-cols-3">
            <Panel
              title="Últimos treinos"
              className="lg:col-span-2"
              action={<SeeAll to="/treinos">Ver todos</SeeAll>}
            >
              {data.recent_sessions.length === 0 ? (
                <Empty
                  title="Nenhum treino registrado ainda"
                  text="Registre o primeiro treino para acompanhar a evolução."
                  to="/treinos/novo"
                  cta="Registrar treino"
                />
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full min-w-[34rem] text-left text-sm">
                    <thead className="text-xs uppercase tracking-wide text-muted">
                      <tr>
                        <th scope="col" className="px-5 py-3 font-medium">Atleta</th>
                        <th scope="col" className="px-5 py-3 font-medium">Data</th>
                        <th scope="col" className="px-5 py-3 font-medium">Prova</th>
                        <th scope="col" className="px-5 py-3 font-medium">Tempo</th>
                        <th scope="col" className="px-5 py-3">
                          <span className="sr-only">Ações</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.recent_sessions.map((session) => (
                        <tr key={session.id} className="border-t border-line">
                          <td className="px-5 py-3">
                            <div className="flex items-center gap-3">
                              <span
                                aria-hidden="true"
                                className="grid size-8 shrink-0 place-items-center rounded-full bg-brand-soft text-xs font-semibold text-brand-text"
                              >
                                {initials(session.athlete_name)}
                              </span>
                              <span className="font-medium">{session.athlete_name}</span>
                            </div>
                          </td>
                          <td className="px-5 py-3 text-muted">
                            {formatDate(session.session_date)}
                          </td>
                          <td className="px-5 py-3">{formatRace(session)}</td>
                          <td className="px-5 py-3 font-semibold">
                            {formatTime(session.total_time_s)}
                          </td>
                          <td className="px-5 py-3 text-right">
                            <Link
                              to={`/treinos/${session.athlete_id}/${session.id}`}
                              className="inline-flex items-center gap-1 font-medium text-brand-text hover:underline"
                            >
                              Ver detalhes
                              <ArrowRight size={14} aria-hidden="true" />
                              <span className="sr-only">
                                {' '}
                                de {session.athlete_name} em {formatDate(session.session_date)}
                              </span>
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </Panel>

            <Panel title="Atletas" action={<SeeAll to="/atletas">Ver todos</SeeAll>}>
              {data.athletes.length === 0 ? (
                <Empty
                  title="Nenhum atleta ativo"
                  text="Cadastre um atleta para começar."
                  to="/atletas/novo"
                  cta="Cadastrar atleta"
                />
              ) : (
                <ul className="divide-y divide-line">
                  {data.athletes.map((athlete) => (
                    <li key={athlete.id} className="flex items-center gap-3 px-5 py-3">
                      <span
                        aria-hidden="true"
                        className="grid size-9 shrink-0 place-items-center rounded-full bg-brand-soft text-xs font-semibold text-brand-text"
                      >
                        {initials(athlete.name)}
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-medium">{athlete.name}</p>
                        <p className="text-xs text-muted">
                          {athlete.last_session_date
                            ? `Último treino ${formatDaysAgo(athlete.last_session_date)} (${formatDate(athlete.last_session_date)})`
                            : 'Sem treinos registrados'}
                        </p>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </Panel>
          </div>
        </>
      )}
    </>
  )
}