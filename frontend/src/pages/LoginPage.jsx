import { useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function LoginPage() {
  const { coach, signIn } = useAuth()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const from = location.state?.from?.pathname ?? '/atletas'
  if (coach) return <Navigate to={from} replace />

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await signIn(email, password)
    } catch (err) {
      setError(err.message)
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <h1>Entrar</h1>
      <input type="email" placeholder="E-mail" value={email}
        onChange={(e) => setEmail(e.target.value)} required />
      <input type="password" placeholder="Senha" value={password}
        onChange={(e) => setPassword(e.target.value)} required />
      <button disabled={submitting}>{submitting ? 'Entrando…' : 'Entrar'}</button>
      {error && <p role="alert">{error}</p>}
    </form>
  )
}