import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import PageHeader from '../components/PageHeader'
import SessionForm from '../components/SessionForm'
import Alert from '../components/ui/Alert'
import { buttonClasses } from '../components/ui/button-styles'
import Spinner from '../components/ui/Spinner'
import { getAthlete } from '../services/athletes'
import { getSession, updateSession } from '../services/sessions'

export default function SessionEditPage() {
  const { athleteId, sessionId } = useParams()
  const navigate = useNavigate()
  const key = `${athleteId}/${sessionId}`
  const [state, setState] = useState({ key: null, athlete: null, session: null, error: '' })
  const loading = state.key !== key

  useEffect(() => {
    let cancelled = false
    Promise.all([getAthlete(athleteId), getSession(athleteId, sessionId)])
      .then(([athlete, session]) => {
        if (!cancelled) setState({ key, athlete, session, error: '' })
      })
      .catch((err) => {
        if (!cancelled) setState({ key, athlete: null, session: null, error: err.message })
      })
    return () => {
      cancelled = true
    }
  }, [athleteId, sessionId, key])

  return (
    <>
      <PageHeader title="Editar treino" description="Atualize os dados do registro." />
      {loading ? (
        <Spinner />
      ) : state.error ? (
        <div className="max-w-xl space-y-4">
          <Alert>{state.error}</Alert>
          <Link to="/treinos" className={buttonClasses('secondary')}>
            Voltar para treinos
          </Link>
        </div>
      ) : (
        <SessionForm
          key={state.session.id}
          fixedAthlete={state.athlete}
          initial={state.session}
          submitLabel="Salvar alterações"
          onCancel={() => navigate(`/treinos/${athleteId}/${sessionId}`)}
          onSubmit={async (id, payload) => {
            await updateSession(id, state.session.id, payload)
            navigate(`/treinos/${id}/${state.session.id}`)
          }}
        />
      )}
    </>
  )
}