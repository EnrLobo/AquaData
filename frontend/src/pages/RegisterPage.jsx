import { useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import AuthShell from '../components/AuthShell'
import Logo from '../components/Logo'
import Alert from '../components/ui/Alert'
import Button from '../components/ui/Button'
import PasswordField from '../components/ui/PasswordField'
import TextField from '../components/ui/TextField'
import { useAuth } from '../hooks/useAuth'
import { register } from '../services/auth'

export default function RegisterPage() {
  const { coach, signIn } = useAuth()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (coach) return <Navigate to="/atletas" replace />

  async function handleSubmit(event) {
    event.preventDefault()
    const cleanName = name.trim().replace(/\s+/g, ' ')
    if (cleanName.length < 2) return setError('Informe seu nome (mínimo de 2 caracteres)')
    if (password.length < 8) return setError('A senha deve ter ao menos 8 caracteres')
    if (password !== confirm) return setError('As senhas não conferem')

    setError('')
    setSubmitting(true)
    try {
      await register({ name: cleanName, email, password })
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
        <h1 className="mt-8 text-center text-3xl font-bold tracking-tight">Crie sua conta</h1>
        <form onSubmit={handleSubmit} noValidate className="mt-8 space-y-4">
          <TextField
            id="name"
            label="Nome"
            hideLabel
            placeholder="Seu nome"
            value={name}
            maxLength={120}
            autoComplete="name"
            onChange={(e) => setName(e.target.value)}
          />
          <TextField
            id="email"
            type="email"
            label="E-mail"
            hideLabel
            placeholder="Insira seu e-mail"
            value={email}
            autoComplete="email"
            onChange={(e) => setEmail(e.target.value)}
          />
          <PasswordField
            id="password"
            label="Senha"
            hideLabel
            placeholder="Crie uma senha (mín. 8 caracteres)"
            value={password}
            autoComplete="new-password"
            onChange={(e) => setPassword(e.target.value)}
          />
          <PasswordField
            id="confirm"
            label="Confirmar senha"
            hideLabel
            placeholder="Repita a senha"
            value={confirm}
            autoComplete="new-password"
            onChange={(e) => setConfirm(e.target.value)}
          />
          {error && <Alert>{error}</Alert>}
          <Button type="submit" className="w-full" disabled={submitting}>
            {submitting ? 'Criando conta…' : 'Criar conta'}
          </Button>
        </form>
        <p className="mt-6 text-center text-sm text-muted">
          Já possui uma conta?{' '}
          <Link to="/login" className="font-semibold text-brand-text hover:underline">
            Fazer login
          </Link>
        </p>
      </div>
    </AuthShell>
  )
}