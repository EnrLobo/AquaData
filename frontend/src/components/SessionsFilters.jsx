import { SESSION_TYPE_LABEL, STROKE_LABEL } from '../utils/session'
import Button from './ui/Button'
import Select from './ui/Select'
import TextField from './ui/TextField'

const toOptions = (labels, all) => [
  { value: '', label: all },
  ...Object.entries(labels).map(([value, label]) => ({ value, label })),
]

const STROKE_OPTIONS = toOptions(STROKE_LABEL, 'Todos os nados')
const TYPE_OPTIONS = toOptions(SESSION_TYPE_LABEL, 'Todos os tipos')

export default function SessionFilters({ id, filters, onChange, onClear }) {
  const set = (field) => (value) => onChange({ ...filters, [field]: value })

  return (
    <div
      id={id}
      className="mb-6 grid gap-4 rounded-2xl border border-line bg-surface p-5 sm:grid-cols-2 lg:grid-cols-5 lg:items-end"
    >
      <Select
        id="f-stroke"
        label="Nado"
        hideLabel={false}
        options={STROKE_OPTIONS}
        value={filters.stroke}
        onChange={set('stroke')}
      />
      <Select
        id="f-type"
        label="Tipo"
        hideLabel={false}
        options={TYPE_OPTIONS}
        value={filters.sessionType}
        onChange={set('sessionType')}
      />
      <TextField
        id="f-from"
        type="date"
        label="De"
        value={filters.dateFrom}
        onChange={(e) => set('dateFrom')(e.target.value)}
      />
      <TextField
        id="f-to"
        type="date"
        label="Até"
        value={filters.dateTo}
        onChange={(e) => set('dateTo')(e.target.value)}
      />
      <Button variant="ghost" onClick={onClear}>
        Limpar filtros
      </Button>
    </div>
  )
}