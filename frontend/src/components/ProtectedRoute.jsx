import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import Spinner from './ui/Spinner'

export default function ProtectedRoute() {
  const { coach, loading } = useAuth()
  const location = useLocation()

  if (loading) return <Spinner />
  if (!coach) return <Navigate to="/login" replace state={{ from: location }} />
  return <Outlet />
}