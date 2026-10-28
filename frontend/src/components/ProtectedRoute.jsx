import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'

export default function ProtectedRoute() {
  const { coach, loading } = useAuth()
  const location = useLocation()

  if (loading) return <p>Carregando…</p>
  if (!coach) return <Navigate to="/login" replace state={{ from: location }} />
  return <Outlet />
}