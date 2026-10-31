import { Plus } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import AthleteCard from '../components/AthleteCard'
import PageHeader from '../components/PageHeader'
import Alert from '../components/ui/Alert'
import ChipGroup from '../components/ui/ChipGroup'
import { buttonClasses } from '../components/ui/button-styles'
import SearchField from '../components/ui/SearchField'
import Select from '../components/ui/Select'
import Spinner from '../components/ui/Spinner'
import { listAthletes, updateAthlete } from '../services/athletes'

const LIMIT = 100

const STATUS_OPTIONS = [
  { value: 'active', label: 'Ativos' },
  { value: 'inactive', label: 'Inativos' },
  { value: 'all', label: 'Todos' },
]

const SORT_OPTIONS = [
  { value: 'name', label: 'Ordenar: Nome' },
  { value: 'age', label: 'Ordenar: Idade' },
  { value: 'recent', label: 'Ordenar: Mais recentes' },
]

const SORTERS = {
  name: (a, b) => a.name.localeCompare(b.name, 'pt-BR'),
  age: (a, b) => b.birth_date.localeCompare(a.birth_date),
  recent: (a, b) => b.created_at.localeCompare(a.created_at),
}

const queryKey = (status, search) => `${status}|${search}`
const activeParam = (status) => (status === 'all' ? undefined : status === 'active')

function describe(count, status, hasMore) {
  const n = hasMore ? `${count}+` : count
  const one = count === 1
  if (status === 'active') return `${n} ${one ? 'atleta' : 'atletas'} sob sua orientação`
  if (status === 'inactive') return `${n} ${one ? 'atleta inativo' : 'atletas inativos'}`
  return `${n} ${one ? 'atleta cadastrado' : 'atletas cadastrados'}`
}

export default function AthletesPage() {
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('active')
  const [sort, setSort] = useState('name')
  const [result, setResult] = useState({ key: null, items: [], hasMore: false, error: '' })
  const [actionError, setActionError] = useState('')
  const [busyId, setBusyId] = useState(null)

  const loading = result.key !== queryKey(status, search)

  useEffect(() => {
    const id = setTimeout(() => setSearch(searchInput), 300)
    return () => clearTimeout(id)
  }, [searchInput])

  useEffect(() => {
    let cancelled = false
    const key = queryKey(status, search)
    listAthletes({ active: activeParam(status), search, limit: LIMIT })
      .then((data) => {
        if (!cancelled) setResult({ key, items: data, hasMore: data.length === LIMIT, error: '' })
      })
      .catch((err) => {
        if (!cancelled) setResult({ key, items: [], hasMore: false, error: err.message })
      })
    return () => {
      cancelled = true
    }
  }, [status, search])

  const sorted = useMemo(() => [...result.items].sort(SORTERS[sort]), [result.items, sort])

  async function toggleActive(athlete) {
    setBusyId(athlete.id)
    setActionError('')
    try {
      const updated = await updateAthlete(athlete.id, { active: !athlete.active })
      setResult((r) => ({
        ...r,
        items:
          status === 'all'
            ? r.items.map((a) => (a.id === updated.id ? updated : a))
            : r.items.filter((a) => a.id !== updated.id),
      }))
    } catch (err) {
      setActionError(err.message)
    } finally {
      setBusyId(null)
    }
  }

  const filtering = search.trim() !== '' || status !== 'active'

  return (
    <>
      <PageHeader
        title="Meus atletas"
        description={loading ? 'Carregando atletas…' : describe(sorted.length, status, result.hasMore)}
      >
        <Link to="/atletas/novo" className={buttonClasses('primary')}>
          <Plus size={16} aria-hidden="true" />
          Novo atleta
        </Link>
      </PageHeader>

      <div className="mb-8 flex flex-wrap items-center gap-3">
        <SearchField
          id="search"
          label="Buscar atleta por nome"
          placeholder="Buscar atleta por nome"
          value={searchInput}
          maxLength={120}
          onChange={(e) => setSearchInput(e.target.value)}
          className="w-full md:w-96"
        />
        <ChipGroup
          options={STATUS_OPTIONS}
          value={status}
          onChange={setStatus}
          ariaLabel="Filtrar por situação"
        />
        <Select
          id="sort"
          label="Ordenar atletas"
          options={SORT_OPTIONS}
          value={sort}
          onChange={setSort}
          className="w-full sm:ml-auto sm:w-56"
        />
      </div>

      {actionError && (
        <div className="mb-4">
          <Alert>{actionError}</Alert>
        </div>
      )}

      {loading ? (
        <Spinner />
      ) : result.error ? (
        <Alert>{result.error}</Alert>
      ) : sorted.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-line bg-surface py-16 text-center">
          <p className="font-medium">
            {filtering ? 'Nenhum atleta encontrado' : 'Você ainda não cadastrou atletas'}
          </p>
          <p className="mt-1 text-sm text-muted">
            {filtering
              ? 'Tente outro nome ou outro filtro.'
              : 'Cadastre o primeiro para começar a acompanhar a evolução.'}
          </p>
          {!filtering && (
            <Link to="/atletas/novo" className={buttonClasses('primary', 'md', 'mt-6')}>
              Cadastrar atleta
            </Link>
          )}
        </div>
      ) : (
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
          {sorted.map((athlete) => (
            <AthleteCard
              key={athlete.id}
              athlete={athlete}
              busy={busyId === athlete.id}
              onToggleActive={toggleActive}
            />
          ))}
        </div>
      )}
    </>
  )
}