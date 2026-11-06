import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import SessionForm from '../components/SessionForm'
import Alert from '../components/ui/Alert'
import { buttonClasses } from '../components/ui/button-styles'
import Spinner from '../components/ui/Spinner'
import { listAthletes } from '../services/athletes'
import { createSession } from '../services/sessions'

export default function SessionCreatePage() {
  const navigate = useNavigate()
  const [state, setState] = useState({ loaded: false, athletes: [], error: '' })

  useEffect(() => {
    let cancelled = false
    listAthletes({ active: true, limit: 100 })
      .then((athletes) => {
        if (!cancelled) setState({ loaded: true, athletes, error: '' })
      })
      .catch((err) => {
        if (!cancelled) setState({ loaded: true, athletes: [], error: err.message })
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <>
      <PageHeader
        title="Novo treino"
        description="Registre os dados do treino para calcular as métricas."
      />
      {!state.loaded ? (
        <Spinner />
      ) : state.error ? (
        <Alert>{state.error}</Alert>
      ) : state.athletes.length === 0 ? (
        <div className="max-w-xl rounded-2xl border border-dashed border-line bg-surface p-8 text-center">
          <p className="font-medium">Você não tem atletas ativos</p>
          <p className="mt-1 text-sm text-muted">
            Cadastre ou reative um atleta para registrar treinos.
          </p>
          <Link to="/atletas/novo" className={buttonClasses('primary', 'md', 'mt-6')}>
            Cadastrar atleta
          </Link>
        </div>
      ) : (
        <SessionForm
          athletes={state.athletes}
          submitLabel="Registrar treino"
          onCancel={() => navigate('/treinos')}
          onSubmit={async (athleteId, payload) => {
            await createSession(athleteId, payload)
            navigate('/treinos')
          }}
        />
      )}
    </>
  )
}