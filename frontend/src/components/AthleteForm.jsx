import { useState } from 'react'
import { todayIso } from '../utils/date'
import Alert from './ui/Alert'
import Button from './ui/Button'
import Segmented from './ui/Segmented'
import TextField from './ui/TextField'

const SEX_OPTIONS = [
  { value: 'M', label: 'Masculino' },
  { value: 'F', label: 'Feminino' },
]

export default function AthleteForm({ initial, submitLabel, onSubmit, onCancel }) {
  const [name, setName] = useState(initial?.name ?? '')
  const [birthDate, setBirthDate] = useState(initial?.birth_date ?? '')
  const [sex, setSex] = useState(initial?.sex ?? '')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    const cleanName = name.trim().replace(/\s+/g, ' ')
    if (cleanName.length < 2) return setError('Informe o nome do atleta (mínimo de 2 caracteres)')
    if (!birthDate) return setError('Informe a data de nascimento')
    if (birthDate > todayIso()) return setError('A data de nascimento não pode estar no futuro')
    if (!sex) return setError('Selecione o sexo')

    setError('')
    setSubmitting(true)
    try {
      await onSubmit({ name: cleanName, birth_date: birthDate, sex })
    } catch (err) {
      setError(err.message)
      setSubmitting(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="max-w-xl space-y-5 rounded-2xl border border-line bg-surface p-6 sm:p-8"
    >
      <TextField
        id="name"
        label="Nome completo"
        value={name}
        maxLength={120}
        autoComplete="off"
        onChange={(e) => setName(e.target.value)}
      />
      <TextField
        id="birth_date"
        type="date"
        label="Data de nascimento"
        value={birthDate}
        max={todayIso()}
        onChange={(e) => setBirthDate(e.target.value)}
      />
      <div className="space-y-1.5">
        <span className="text-sm font-medium text-fg">Sexo</span>
        <div>
          <Segmented options={SEX_OPTIONS} value={sex} onChange={setSex} ariaLabel="Sexo" />
        </div>
      </div>
      {error && <Alert>{error}</Alert>}
      <div className="flex gap-3 pt-2">
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