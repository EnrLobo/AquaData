import { ArrowRight, Filter, Plus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import SessionFilters from '../components/SessionsFilters'
import Alert from '../components/ui/Alert'
import Button from '../components/ui/Button'
import { buttonClasses } from '../components/ui/button-styles'
import Dash from '../components/ui/Dash'
import Pagination from '../components/ui/Pagination'
import SearchField from '../components/ui/SearchField'
import Spinner from '../components/ui/Spinner'
import { listSessions } from '../services/sessions'
import { formatDate } from '../utils/date'
import { formatDecimal, formatRace, formatTime } from '../utils/session'
import { initials } from '../utils/text'

const PAGE_SIZE = 10
const EMPTY_FILTERS = { stroke: '', sessionType: '', dateFrom: '', dateTo: '' }
const makeKey = (search, filters, page) => JSON.stringify([search, filters, page])

export default function SessionsPage() {
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [filters, setFilters] = useState(EMPTY_FILTERS)
  const [showFilters, setShowFilters] = useState(false)
  const [page, setPage] = useState(1)
  const [result, setResult] = useState({ key: null, items: [], total: 0, error: '' })

  const loading = result.key !== makeKey(search, filters, page)
  const activeFilters = Object.values(filters).filter(Boolean).length
  const totalPages = Math.max(1, Math.ceil(result.total / PAGE_SIZE))

  useEffect(() => {
    const id = setTimeout(() => {
      setSearch(searchInput)
      setPage(1)
    }, 300)
    return () => clearTimeout(id)
  }, [searchInput])

  useEffect(() => {
    let cancelled = false
    const key = makeKey(search, filters, page)
    listSessions({
      search,
      stroke: filters.stroke,
      sessionType: filters.sessionType,
      dateFrom: filters.dateFrom,
      dateTo: filters.dateTo,
      limit: PAGE_SIZE,
      offset: (page - 1) * PAGE_SIZE,
    })
      .then((data) => {
        if (!cancelled) setResult({ key, items: data.items, total: data.total, error: '' })
      })
      .catch((err) => {
        if (!cancelled) setResult({ key, items: [], total: 0, error: err.message })
      })
    return () => {
      cancelled = true
    }
  }, [search, filters, page])

  function changeFilters(next) {
    setFilters(next)
    setPage(1)
  }

  const filtering = search.trim() !== '' || activeFilters > 0
  const first = (page - 1) * PAGE_SIZE + 1

  return (
    <>
      <PageHeader title="Treinos" description="Histórico de treinos dos seus atletas">
        <Link to="/treinos/novo" className={buttonClasses('primary')}>
          <Plus size={16} aria-hidden="true" />
          Novo treino
        </Link>
      </PageHeader>

      <div className="mb-6 flex flex-wrap items-center gap-3">
        <SearchField
          id="search"
          label="Buscar pelo nome do atleta"
          placeholder="Buscar pelo nome do atleta"
          value={searchInput}
          maxLength={120}
          onChange={(e) => setSearchInput(e.target.value)}
          className="w-full md:w-96"
        />
        <Button
          variant="secondary"
          onClick={() => setShowFilters((v) => !v)}
          aria-expanded={showFilters}
          aria-controls="session-filters"
        >
          <Filter size={16} aria-hidden="true" />
          Filtrar{activeFilters > 0 ? ` (${activeFilters})` : ''}
        </Button>
        {!loading && !result.error && (
          <p className="ml-auto text-sm text-muted">
            {result.total} {result.total === 1 ? 'treino' : 'treinos'}
          </p>
        )}
      </div>

      {showFilters && (
        <SessionFilters
          id="session-filters"
          filters={filters}
          onChange={changeFilters}
          onClear={() => changeFilters(EMPTY_FILTERS)}
        />
      )}

      {loading ? (
        <Spinner />
      ) : result.error ? (
        <Alert>{result.error}</Alert>
      ) : result.items.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-line bg-surface py-16 text-center">
          <p className="font-medium">
            {filtering ? 'Nenhum treino encontrado' : 'Nenhum treino registrado ainda'}
          </p>
          <p className="mt-1 text-sm text-muted">
            {filtering
              ? 'Tente outro nome ou outros filtros.'
              : 'Registre o primeiro treino para começar a acompanhar a evolução.'}
          </p>
          {!filtering && (
            <Link to="/treinos/novo" className={buttonClasses('primary', 'md', 'mt-6')}>
              Registrar treino
            </Link>
          )}
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-2xl border border-line bg-surface">
            <table className="w-full min-w-[52rem] text-left text-sm">
              <thead className="bg-subtle text-xs uppercase tracking-wide text-muted">
                <tr>
                  <th scope="col" className="px-5 py-3 font-medium">Atleta</th>
                  <th scope="col" className="px-5 py-3 font-medium">Data</th>
                  <th scope="col" className="px-5 py-3 font-medium">Prova</th>
                  <th scope="col" className="px-5 py-3 font-medium">Tempo</th>
                  <th scope="col" className="px-5 py-3 font-medium">
                    <abbr title="Tempo total + braçadas da prova completa" className="cursor-help">
                      SWOLF
                    </abbr>
                  </th>
                  <th scope="col" className="px-5 py-3 font-medium">
                    <abbr title="Comprimento de braçada" className="cursor-help">
                      CB
                    </abbr>
                  </th>
                  <th scope="col" className="px-5 py-3 font-medium">
                    <abbr title="Velocidade de nado" className="cursor-help">
                      VN
                    </abbr>
                  </th>
                  <th scope="col" className="px-5 py-3">
                    <span className="sr-only">Ações</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {result.items.map((session) => {
                  const m = session.metrics ?? {}
                  return (
                    <tr key={session.id} className="border-t border-line">
                      <td className="px-5 py-4">
                        <div className="flex items-center gap-3">
                          <span
                            aria-hidden="true"
                            className="grid size-9 shrink-0 place-items-center rounded-full bg-brand-soft text-xs font-semibold text-brand-text"
                          >
                            {initials(session.athlete_name)}
                          </span>
                          <span className="font-semibold">{session.athlete_name}</span>
                        </div>
                      </td>
                      <td className="px-5 py-4 text-muted">{formatDate(session.session_date)}</td>
                      <td className="px-5 py-4">{formatRace(session)}</td>
                      <td className="px-5 py-4 font-semibold">{formatTime(session.total_time_s)}</td>
                      <td className="px-5 py-4">{m.swolf != null ? formatDecimal(m.swolf, 1) : <Dash />}</td>
                      <td className="px-5 py-4">
                        {m.cb != null ? `${formatDecimal(m.cb)} m` : <Dash />}
                      </td>
                      <td className="px-5 py-4">
                        {m.vn != null ? `${formatDecimal(m.vn)} m/s` : <Dash />}
                      </td>
                      <td className="px-5 py-4 text-right">
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
                  )
                })}
              </tbody>
            </table>
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-between gap-3 text-sm text-muted">
            <span>
              Mostrando {first}–{first + result.items.length - 1} de {result.total}{' '}
              {result.total === 1 ? 'treino' : 'treinos'}
            </span>
            <Pagination page={page} totalPages={totalPages} onChange={setPage} />
          </div>
        </>
      )}
    </>
  )
}