import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import AthleteForm from '../components/AthleteForm'
import PageHeader from '../components/PageHeader'
import Alert from '../components/ui/Alert'
import { buttonClasses } from '../components/ui/button-styles'
import Spinner from '../components/ui/Spinner'
import { getAthlete, updateAthlete } from '../services/athletes'

export default function AthleteEditPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [state, setState] = useState({ id: null, athlete: null, error: '' })
  const loading = state.id !== id

  useEffect(() => {
    let cancelled = false
    getAthlete(id)
      .then((athlete) => {
        if (!cancelled) setState({ id, athlete, error: '' })
      })
      .catch((err) => {
        if (!cancelled) setState({ id, athlete: null, error: err.message })
      })
    return () => {
      cancelled = true
    }
  }, [id])

  return (
    <>
      <PageHeader title="Editar atleta" description="Atualize os dados do atleta." />
      {loading ? (
        <Spinner />
      ) : state.error ? (
        <div className="max-w-xl space-y-4">
          <Alert>{state.error}</Alert>
          <Link to="/atletas" className={buttonClasses('secondary')}>
            Voltar para atletas
          </Link>
        </div>
      ) : (
        <AthleteForm
          key={state.athlete.id}
          initial={state.athlete}
          submitLabel="Salvar alterações"
          onCancel={() => navigate('/atletas')}
          onSubmit={async (data) => {
            await updateAthlete(state.athlete.id, data)
            navigate('/atletas')
          }}
        />
      )}
    </>
  )
}