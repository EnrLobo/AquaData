import { useEffect, useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { listAthletes } from '../services/athletes'

export default function AthletesPage() {
  const { coach, signOut } = useAuth()
  const [athletes, setAthletes] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    listAthletes()
      .then(setAthletes)
      .catch((err) => setError(err.message))
  }, [])

  return (
    <main>
      <p>Treinador: {coach.name}</p>
      <button onClick={signOut}>Sair</button>
      {error && <p role="alert">{error}</p>}
      {athletes && <p>{athletes.length} atleta(s) cadastrado(s)</p>}
    </main>
  )
}   