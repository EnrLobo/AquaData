import { useNavigate } from 'react-router-dom'
import AthleteForm from '../components/AthleteForm'
import PageHeader from '../components/PageHeader'
import { createAthlete } from '../services/athletes'

export default function AthleteCreatePage() {
  const navigate = useNavigate()

  return (
    <>
      <PageHeader title="Novo atleta" description="Informe os dados básicos do atleta." />
      <AthleteForm
        submitLabel="Cadastrar atleta"
        onCancel={() => navigate('/atletas')}
        onSubmit={async (data) => {
          await createAthlete(data)
          navigate('/atletas')
        }}
      />
    </>
  )
}