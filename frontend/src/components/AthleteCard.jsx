import { Activity, Pencil, UserCheck, UserX } from 'lucide-react'
import { Link } from 'react-router-dom'
import { calcAge, formatDate, formatDaysAgo } from '../utils/date'
import { formatDecimal, formatRace } from '../utils/session'
import { initials } from '../utils/text'
import Badge from './ui/Badge'
import Button from './ui/Button'
import { buttonClasses } from './ui/button-styles'

const SEX_LABEL = { M: 'Masculino', F: 'Feminino' }

// mesmo selo do painel Início (inclinação da reta do tempo da prova principal)
const STATUS = {
  improving: { label: 'Melhorando', tone: 'success' },
  stable: { label: 'Estável', tone: 'neutral' },
  attention: { label: 'Atenção', tone: 'warning' },
}

function Metric({ label, value, digits, unit }) {
  return (
    <div>
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="mt-1 text-xl font-semibold">
        {value != null ? (
          <>
            {formatDecimal(value, digits)}
            {unit && <span className="ml-1 text-xs font-medium text-muted">{unit}</span>}
          </>
        ) : (
          <span className="text-muted">
            <span aria-hidden="true">—</span>
            <span className="sr-only">sem dados</span>
          </span>
        )}
      </dd>
    </div>
  )
}

function Trend({ trend }) {
  if (!trend) {
    return <p className="text-xs text-muted">Tendência a partir de 6 registros na mesma prova</p>
  }
  const status = trend.status ? STATUS[trend.status] : null
  return (
    <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
      <span>Tendência em {formatRace(trend)}:</span>
      {status ? (
        <Badge tone={status.tone}>{status.label}</Badge>
      ) : (
        <Badge tone="neutral">
          Poucos registros ({trend.n_records} de {trend.min_records})
        </Badge>
      )}
    </div>
  )
}

export default function AthleteCard({ athlete, busy, onToggleActive }) {
  const action = athlete.active ? 'Inativar' : 'Reativar'
  const summary = athlete.summary
  const last = summary?.last_session ?? null

  return (
    <article
      className={`flex flex-col rounded-2xl border border-line bg-surface p-6 transition-shadow hover:shadow-md ${
        athlete.active ? '' : 'opacity-80'
      }`}
    >
      <header className="flex items-start gap-3">
        <span
          aria-hidden="true"
          className="grid size-10 shrink-0 place-items-center rounded-full bg-brand-soft text-xs font-semibold text-brand-text"
        >
          {initials(athlete.name)}
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="truncate font-semibold">{athlete.name}</h2>
          <p className="text-sm text-muted">
            {calcAge(athlete.birth_date)} anos · {SEX_LABEL[athlete.sex]}
          </p>
        </div>
        <Badge tone={athlete.active ? 'success' : 'neutral'}>
          {athlete.active ? 'Ativo' : 'Inativo'}
        </Badge>
      </header>

      <div className="mt-5 border-t border-line pt-5">
        <p className="mb-3 text-xs font-medium text-muted">
          {last
            ? `Último treino: ${formatRace(last)}, ${formatDaysAgo(last.session_date)} (${formatDate(last.session_date)})`
            : 'Sem treinos registrados'}
        </p>
        <dl className="grid grid-cols-3 gap-3">
          <Metric label="SWOLF" value={last?.swolf} digits={1} />
          <Metric label="Braçada (CB)" value={last?.cb} digits={2} unit="m" />
          <Metric label="Velocidade (VN)" value={last?.vn} digits={2} unit="m/s" />
        </dl>
        {last && (
          <div className="mt-4">
            <Trend trend={summary.main_trend} />
          </div>
        )}
      </div>

      <footer className="mt-auto flex items-center justify-between gap-2 pt-5 text-sm">
        <span className="text-muted">
          {summary
            ? `${summary.sessions_count} ${summary.sessions_count === 1 ? 'registro' : 'registros'}`
            : ''}
        </span>
        <div className="flex gap-1">
          <Link
            to={`/desempenho/${athlete.id}`}
            className={buttonClasses('ghost', 'icon')}
            aria-label={`Ver desempenho de ${athlete.name}`}
            title="Ver desempenho"
          >
            <Activity size={16} aria-hidden="true" />
          </Link>
          <Link
            to={`/atletas/${athlete.id}/editar`}
            className={buttonClasses('ghost', 'icon')}
            aria-label={`Editar ${athlete.name}`}
            title="Editar"
          >
            <Pencil size={16} aria-hidden="true" />
          </Link>
          <Button
            variant="ghost"
            size="icon"
            disabled={busy}
            onClick={() => onToggleActive(athlete)}
            aria-label={`${action} ${athlete.name}`}
            title={action}
          >
            {athlete.active ? (
              <UserX size={16} aria-hidden="true" />
            ) : (
              <UserCheck size={16} aria-hidden="true" />
            )}
          </Button>
        </div>
      </footer>
    </article>
  )
}