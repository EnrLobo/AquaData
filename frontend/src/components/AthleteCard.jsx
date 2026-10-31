import { Pencil, UserCheck, UserX } from 'lucide-react'
import { Link } from 'react-router-dom'
import { initials } from '../utils/text'
import { calcAge } from '../utils/date'
import Badge from './ui/Badge'
import Button from './ui/Button'
import { buttonClasses } from './ui/button-styles'

const SEX_LABEL = { M: 'Masculino', F: 'Feminino' }

function Metric({ label, value }) {
  return (
    <div>
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="mt-1 text-xl font-semibold text-muted">
        {value ?? (
          <>
            <span aria-hidden="true">—</span>
            <span className="sr-only">sem dados</span>
          </>
        )}
      </dd>
    </div>
  )
}

export default function AthleteCard({ athlete, busy, onToggleActive }) {
  const action = athlete.active ? 'Inativar' : 'Reativar'

  return (
    <article
      className={`rounded-2xl border border-line bg-surface p-6 transition-shadow hover:shadow-md ${
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

      <dl className="mt-5 grid grid-cols-3 gap-3 border-t border-line pt-5">
        <Metric label="SWOLF" />
        <Metric label="Braçada (CB)" />
        <Metric label="Velocidade (VN)" />
      </dl>

      <footer className="mt-5 flex items-center justify-between gap-2 text-sm">
        <span className="text-muted">Sem treinos registrados</span>
        <div className="flex gap-1">
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