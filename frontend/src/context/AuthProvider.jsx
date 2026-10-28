import { useCallback, useEffect, useMemo, useState } from 'react'
import { AuthContext } from './auth-context'
import { setUnauthorizedHandler, tokenStorage } from '../services/api'
import * as authService from '../services/auth'

export default function AuthProvider({ children }) {
  const [coach, setCoach] = useState(null)
  const [loading, setLoading] = useState(() => Boolean(tokenStorage.get()))

  const signOut = useCallback(() => {
    authService.logout()
    setCoach(null)
  }, [])

  useEffect(() => {
    setUnauthorizedHandler(signOut)
    if (!tokenStorage.get()) return
    let cancelled = false
    authService
      .fetchMe()
      .then((me) => {
        if (!cancelled) setCoach(me)
      })
      .catch(() => {})
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [signOut])

  const signIn = useCallback(async (email, password) => {
    setCoach(await authService.login(email, password))
  }, [])

  const value = useMemo(
    () => ({ coach, loading, signIn, signOut }),
    [coach, loading, signIn, signOut],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}