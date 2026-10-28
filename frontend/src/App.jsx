import { Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/ProtectedRoute'
import AthletesPage from './pages/AthletesPage'
import LoginPage from './pages/LoginPage'

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route element={<ProtectedRoute />}>
        <Route path="/atletas" element={<AthletesPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/atletas" replace />} />
    </Routes>
  )
}