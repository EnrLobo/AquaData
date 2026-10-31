import { LogIn } from 'lucide-react'
import { useState } from 'react'
import { Link, Navigate, useLocation } from 'react-router-dom'
import AuthShell from '../components/AuthShell'
import Logo from '../components/Logo'
import Alert from '../components/ui/Alert'
import Button from '../components/ui/Button'
import PasswordField from '../components/ui/PasswordField'
import TextField from '../components/ui/TextField'
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
    <AuthShell>
      <div className="rounded-3xl border border-line bg-surface p-8 shadow-[0_12px_40px_-16px_rgba(11,58,87,0.35)] sm:p-10">
        <div className="flex justify-center">
          <Logo className="h-12" />
        </div>
        <h1 className="mt-8 text-center text-3xl font-bold tracking-tight">Boas Vindas!</h1>
        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          <TextField
            id="email"
            type="email"
            label="E-mail"
            hideLabel
            placeholder="Insira seu e-mail"
            value={email}
            autoComplete="email"
            required
            onChange={(e) => setEmail(e.target.value)}
          />
          <PasswordField
            id="password"
            label="Senha"
            hideLabel
            placeholder="Sua senha"
            value={password}
            autoComplete="current-password"
            required
            onChange={(e) => setPassword(e.target.value)}
          />
          {error && <Alert>{error}</Alert>}
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? (
              'Entrando…'
            ) : (
              <>
                Fazer login <LogIn size={16} aria-hidden="true" />
              </>
            )}
          </Button>
        </form>
        <p className="mt-6 text-center text-sm text-muted">
          Ainda não possui uma conta?{' '}
          <Link to="/cadastro" className="font-semibold text-brand-text hover:underline">
            Cadastre-se
          </Link>
        </p>
      </div>
    </AuthShell>
  )
}