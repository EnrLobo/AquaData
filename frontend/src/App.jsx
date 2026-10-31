import { Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from './components/AppLayout'
import ProtectedRoute from './components/ProtectedRoute'
import AthleteCreatePage from './pages/AthleteCreatePage'
import AthleteEditPage from './pages/AthleteEditPage'
import AthletesPage from './pages/AthletesPage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'


export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/atletas" element={<AthletesPage />} />
          <Route path="/atletas/novo" element={<AthleteCreatePage />} />
          <Route path="/atletas/:id/editar" element={<AthleteEditPage />} />
          <Route path="/cadastro" element={<RegisterPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/atletas" replace />} />
    </Routes>
  )
}