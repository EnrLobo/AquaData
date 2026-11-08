import { useState } from 'react'
import { todayIso } from '../utils/date'
import { formatTime, parseDecimal, parseInteger, parseTime } from '../utils/session'
import Alert from './ui/Alert'
import Button from './ui/Button'
import Segmented from './ui/Segmented'
import Select from './ui/Select'
import TextField from './ui/TextField'

const MAX_SPLITS = 20
const GUARD_M = 10 // 5 m de cada borda (bandeirolas)

const TYPE_OPTIONS = [
  { value: 'training', label: 'Treino' },
  { value: 'competition', label: 'Competição' },
]
const POOL_OPTIONS = [
  { value: '25', label: '25 m' },
  { value: '50', label: '50 m' },
]
const MODE_OPTIONS = [
  { value: 'splits', label: 'Por extensão' },
  { value: 'totals', label: 'Totais' },
]
const STROKE_OPTIONS = [
  { value: '', label: 'Selecione o nado' },
  { value: 'freestyle', label: 'Livre' },
  { value: 'backstroke', label: 'Costas' },
  { value: 'breaststroke', label: 'Peito' },
  { value: 'butterfly', label: 'Borboleta' },
  { value: 'medley', label: 'Medley' },
]

function initialValues(initial, fixedAthlete) {
  return {
    athleteId: fixedAthlete ? String(fixedAthlete.id) : '',
    sessionType: initial?.session_type ?? 'training',
    date: initial?.session_date ?? todayIso(),
    stroke: initial?.stroke ?? '',
    pool: initial ? String(initial.pool_length_m) : '25',
    distance: initial ? String(initial.distance_m) : '',
    totalTime: initial ? formatTime(initial.total_time_s) : '',
    totalCycles: initial?.total_cycle_count != null ? String(initial.total_cycle_count) : '',
    swimDistance: initial ? String(initial.swim_distance_m).replace('.', ',') : '',
    swimTime: initial ? formatTime(initial.swim_time_s) : '',
    cycles: initial ? String(initial.stroke_count) : '',
    notes: initial?.notes ?? '',
  }
}

function countLengths(distance, pool) {
  const d = parseInteger(distance)
  const p = Number(pool)
  return d && d % p === 0 ? d / p : 0
}

function suggestSwimDistance(distance, pool) {
  const lengths = countLengths(distance, pool)
  return lengths ? String(lengths * (Number(pool) - GUARD_M)).replace('.', ',') : ''
}

function sumSplits(splits, lengths) {
  let centiseconds = 0
  let cycles = 0
  let filled = 0
  for (let i = 0; i < lengths; i += 1) {
    const time = parseTime(splits[i]?.time ?? '')
    const count = parseInteger(splits[i]?.cycles ?? '')
    if (time !== null && count !== null) {
      centiseconds += Math.round(time * 100)
      cycles += count
      filled += 1
    }
  }
  return { time: centiseconds / 100, cycles, filled }
}

function buildPayload(v, mode, splits) {
  if (!v.athleteId) return { error: 'Selecione o atleta' }
  if (!v.stroke) return { error: 'Selecione o nado' }
  if (!v.date) return { error: 'Informe a data' }
  if (v.date > todayIso()) return { error: 'A data não pode estar no futuro' }

  const pool = Number(v.pool)
  const distance = parseInteger(v.distance)
  if (!distance) return { error: 'Informe a distância total, em metros' }
  if (distance % pool !== 0) {
    return { error: `A distância deve ser múltipla do tamanho da piscina (${pool} m)` }
  }

  const total = parseTime(v.totalTime)
  if (total === null) return { error: 'Informe o tempo total no formato 1:02,45' }

  const totalCycles = parseInteger(v.totalCycles)
  if (!totalCycles) {
    return { error: 'Informe os ciclos de braçada da prova completa (base do SWOLF)' }
  }

  let swimDistance
  let swimTime
  let cycles

  if (mode === 'splits') {
    const lengths = distance / pool
    if (lengths > MAX_SPLITS) {
      return { error: 'Prova longa demais para o modo por extensão. Use o modo Totais.' }
    }
    const sums = sumSplits(splits, lengths)
    if (sums.filled < lengths) {
      return {
        error: `Preencha tempo e ciclos de todas as extensões (faltam ${lengths - sums.filled}).`,
      }
    }
    swimDistance = lengths * (pool - GUARD_M)
    swimTime = sums.time
    cycles = sums.cycles
  } else {
    swimDistance = parseDecimal(v.swimDistance)
    if (!swimDistance) return { error: 'Informe a distância do trecho de nado puro' }
    swimTime = parseTime(v.swimTime)
    if (swimTime === null) {
      return { error: 'Informe o tempo do trecho de nado puro (ex.: 0:40,20)' }
    }
    cycles = parseInteger(v.cycles)
    if (!cycles) {
      return { error: 'Informe os ciclos de braçada contados no trecho de nado puro' }
    }
  }

  if (swimDistance > distance) {
    return { error: 'O trecho de nado puro não pode superar a distância total' }
  }
  if (swimTime > total) {
    return {
      error: `O tempo do trecho (${formatTime(swimTime)}) não pode superar o tempo total (${formatTime(total)})`,
    }
  }
  if (totalCycles < cycles) {
    return {
      error: `Os ciclos da prova completa (${totalCycles}) não podem ser menos que os do trecho de nado puro (${cycles})`,
    }
  }

  return {
    payload: {
      session_date: v.date,
      session_type: v.sessionType,
      stroke: v.stroke,
      pool_length_m: pool,
      distance_m: distance,
      total_time_s: total,
      stroke_count: cycles,
      total_cycle_count: totalCycles,
      swim_distance_m: swimDistance,
      swim_time_s: swimTime,
      notes: v.notes.trim() || null,
    },
  }
}

function Section({ title, description, children }) {
  return (
    <section className="space-y-4">
      <div>
        <h2 className="text-base font-semibold">{title}</h2>
        {description && <p className="mt-1 text-sm text-muted">{description}</p>}
      </div>
      <div className="grid gap-4 sm:grid-cols-2">{children}</div>
    </section>
  )
}

function SegmentedField({ label, ...props }) {
  return (
    <div className="space-y-1.5">
      <span className="text-sm font-medium text-fg">{label}</span>
      <div>
        <Segmented ariaLabel={label} {...props} />
      </div>
    </div>
  )
}

export default function SessionForm({
  athletes = [],
  fixedAthlete,
  initial,
  submitLabel,
  onSubmit,
  onCancel,
}) {
  const [form, setForm] = useState(() => initialValues(initial, fixedAthlete))
  const [mode, setMode] = useState(initial ? 'totals' : 'splits')
  const [splits, setSplits] = useState({})
  const [swimTouched, setSwimTouched] = useState(Boolean(initial))
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const set = (field) => (value) => setForm((f) => ({ ...f, [field]: value }))
  const onText = (field) => (e) => set(field)(e.target.value)

  function changeRace(field, value) {
    setForm((f) => {
      const next = { ...f, [field]: value }
      if (!swimTouched) next.swimDistance = suggestSwimDistance(next.distance, next.pool)
      return next
    })
  }

  function setSplit(index, field, value) {
    setSplits((s) => ({ ...s, [index]: { time: '', cycles: '', ...s[index], [field]: value } }))
  }

  const poolNumber = Number(form.pool)
  const lengths = countLengths(form.distance, form.pool)
  const sums = sumSplits(splits, lengths)

  const athleteOptions = [
    { value: '', label: 'Selecione o atleta' },
    ...athletes.map((a) => ({ value: String(a.id), label: a.name })),
  ]

  async function handleSubmit(event) {
    event.preventDefault()
    const { error: validationError, payload } = buildPayload(form, mode, splits)
    if (validationError) return setError(validationError)

    setError('')
    setSubmitting(true)
    try {
      await onSubmit(Number(form.athleteId), payload)
    } catch (err) {
      setError(err.message)
      setSubmitting(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="max-w-3xl space-y-8 rounded-2xl border border-line bg-surface p-6 sm:p-8"
    >
      <Section title="Identificação">
        {fixedAthlete ? (
          <TextField id="athlete-fixed" label="Atleta" value={fixedAthlete.name} readOnly disabled />
        ) : (
          <Select
            id="athlete"
            label="Atleta"
            hideLabel={false}
            options={athleteOptions}
            value={form.athleteId}
            onChange={set('athleteId')}
          />
        )}
        <SegmentedField
          label="Tipo"
          options={TYPE_OPTIONS}
          value={form.sessionType}
          onChange={set('sessionType')}
        />
        <TextField
          id="date"
          type="date"
          label="Data"
          value={form.date}
          max={todayIso()}
          onChange={onText('date')}
        />
        <Select
          id="stroke"
          label="Nado"
          hideLabel={false}
          options={STROKE_OPTIONS}
          value={form.stroke}
          onChange={set('stroke')}
        />
      </Section>

      <Section title="Prova">
        <SegmentedField
          label="Piscina"
          options={POOL_OPTIONS}
          value={form.pool}
          onChange={(value) => changeRace('pool', value)}
        />
        <TextField
          id="distance"
          label="Distância total (m)"
          inputMode="numeric"
          value={form.distance}
          hint="Deve ser múltipla do tamanho da piscina."
          onChange={(e) => changeRace('distance', e.target.value)}
        />
        <TextField
          id="total-time"
          label="Tempo total"
          inputMode="text"
          placeholder="1:02,45"
          value={form.totalTime}
          hint="Tempo da prova inteira, em minutos:segundos,centésimos. Ex.: 1:02,45 ou 29,38."
          onChange={onText('totalTime')}
        />
        <TextField
          id="total-cycles"
          label="Ciclos na prova completa"
          inputMode="numeric"
          value={form.totalCycles}
          hint="Todos os ciclos de braçada da prova, com saída e viradas. Base do SWOLF."
          onChange={onText('totalCycles')}
        />
      </Section>

      <section className="space-y-4">
        <div>
          <h2 className="text-base font-semibold">Trecho de nado puro</h2>
          <p className="mt-1 text-sm text-muted">
            Trecho nadado entre as bandeirolas, sem a saída e sem as viradas (5 m de cada borda).
            É a base de VN, CB, cadência e IN. Os dois braços juntos contam 1 ciclo.
          </p>
        </div>

        <SegmentedField
          label="Como informar"
          options={MODE_OPTIONS}
          value={mode}
          onChange={setMode}
        />

        {mode === 'splits' ? (
          lengths === 0 ? (
            <p className="rounded-xl bg-subtle px-4 py-3 text-sm text-muted">
              Informe a distância total (múltipla do tamanho da piscina) para listar as extensões.
            </p>
          ) : lengths > MAX_SPLITS ? (
            <p className="rounded-xl bg-subtle px-4 py-3 text-sm text-muted">
              Esta prova tem {lengths} extensões. Para provas longas, use o modo Totais.
            </p>
          ) : (
            <>
              <div className="space-y-3">
                <div className="hidden grid-cols-[1.2fr_1fr_1fr] gap-3 text-xs font-medium uppercase tracking-wide text-muted sm:grid">
                  <span>Extensão</span>
                  <span>Tempo do trecho</span>
                  <span>Ciclos</span>
                </div>
                {Array.from({ length: lengths }, (_, index) => (
                  <div
                    key={index}
                    className="grid items-center gap-3 sm:grid-cols-[1.2fr_1fr_1fr]"
                  >
                    <span className="text-sm font-medium">
                      {index + 1}ª extensão{' '}
                      <span className="font-normal text-muted">
                        ({index * poolNumber}–{(index + 1) * poolNumber} m)
                      </span>
                    </span>
                    <div>
                      <span aria-hidden="true" className="mb-1 block text-xs text-muted sm:hidden">
                        Tempo do trecho
                      </span>
                      <TextField
                        id={`split-time-${index}`}
                        label={`Extensão ${index + 1}: tempo do trecho`}
                        hideLabel
                        inputMode="text"
                        placeholder="10,50"
                        value={splits[index]?.time ?? ''}
                        onChange={(e) => setSplit(index, 'time', e.target.value)}
                      />
                    </div>
                    <div>
                      <span aria-hidden="true" className="mb-1 block text-xs text-muted sm:hidden">
                        Ciclos
                      </span>
                      <TextField
                        id={`split-cycles-${index}`}
                        label={`Extensão ${index + 1}: ciclos de braçada`}
                        hideLabel
                        inputMode="numeric"
                        placeholder="8"
                        value={splits[index]?.cycles ?? ''}
                        onChange={(e) => setSplit(index, 'cycles', e.target.value)}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <p className="rounded-xl bg-subtle px-4 py-3 text-sm" aria-live="polite">
                <strong>Resumo do trecho:</strong> {lengths * (poolNumber - GUARD_M)} m ·{' '}
                {sums.filled > 0 ? formatTime(sums.time) : '—'} · {sums.cycles} ciclos ·{' '}
                {sums.filled}/{lengths} extensões preenchidas
              </p>
              {initial && (
                <p className="text-xs text-muted">
                  Os valores por extensão não são guardados, só os totais. Para editar por
                  extensão, preencha todas de novo.
                </p>
              )}
            </>
          )
        ) : (
          <div className="grid gap-4 sm:grid-cols-2">
            <TextField
              id="swim-distance"
              label="Distância do trecho (m)"
              inputMode="decimal"
              value={form.swimDistance}
              hint="Sugerida pelo padrão: bandeirolas a 5 m de cada borda. Edite se medir de outra forma."
              onChange={(e) => {
                setSwimTouched(true)
                set('swimDistance')(e.target.value)
              }}
            />
            <TextField
              id="swim-time"
              label="Tempo do trecho"
              inputMode="text"
              placeholder="0:40,20"
              value={form.swimTime}
              hint="Soma dos tempos de todas as extensões."
              onChange={onText('swimTime')}
            />
            <TextField
              id="cycles"
              label="Ciclos de braçada"
              inputMode="numeric"
              value={form.cycles}
              hint="Soma dos ciclos de todas as extensões."
              onChange={onText('cycles')}
            />
          </div>
        )}
      </section>

      <section className="space-y-1.5">
        <label htmlFor="notes" className="text-sm font-medium text-fg">
          Observações (opcional)
        </label>
        <textarea
          id="notes"
          value={form.notes}
          maxLength={1000}
          onChange={onText('notes')}
          className="min-h-24 w-full rounded-xl border border-accent/40 bg-bg px-4 py-3 text-sm text-fg placeholder:text-muted focus:border-brand focus:outline-2 focus:outline-accent/40"
        />
      </section>

      {error && <Alert>{error}</Alert>}
      <div className="flex gap-3">
        <Button type="submit" disabled={submitting}>
          {submitting ? 'Salvando…' : submitLabel}
        </Button>
        <Button variant="secondary" onClick={onCancel} disabled={submitting}>
          Cancelar
        </Button>
      </div>
    </form>
  )
}