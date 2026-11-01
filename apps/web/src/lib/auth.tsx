import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { api, clearSession, getIsDemoSession, getStoredToken, storeSession } from './api-client'
import { DEMO_BUSINESS_SLUG } from './config'
import { getTelegramWebApp, isRunningInTelegram } from './telegram'

interface AuthState {
  status: 'loading' | 'ready' | 'error'
  isDemo: boolean
  isTelegram: boolean
  error: string | null
  retry: () => void
}

const AuthContext = createContext<AuthState | null>(null)

/**
 * Resolves a BookFlow session token before anything else renders:
 *  - inside Telegram, exchange the real, signed initData for a token
 *  - everywhere else (a plain browser tab), fall back to demo mode,
 *    scoped to the seeded ATELIER business, per spec section 19.
 * A token already in localStorage from a previous visit is reused as-is
 * rather than re-authenticating on every load.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<Omit<AuthState, 'retry'>>({
    status: 'loading',
    isDemo: getIsDemoSession(),
    isTelegram: isRunningInTelegram(),
    error: null,
  })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false

    async function authenticate() {
      setState((s) => ({ ...s, status: 'loading', error: null }))

      if (getStoredToken()) {
        if (!cancelled) setState((s) => ({ ...s, status: 'ready' }))
        return
      }

      try {
        const webApp = getTelegramWebApp()
        if (webApp) {
          webApp.ready()
          webApp.expand()
          const token = await api.authTelegram({ init_data: webApp.initData })
          storeSession(token.access_token, token.is_demo)
          if (!cancelled) setState({ status: 'ready', isDemo: false, isTelegram: true, error: null })
        } else {
          const token = await api.authDemo({ business_slug: DEMO_BUSINESS_SLUG })
          storeSession(token.access_token, token.is_demo)
          if (!cancelled) setState({ status: 'ready', isDemo: true, isTelegram: false, error: null })
        }
      } catch (err) {
        if (!cancelled) {
          setState((s) => ({
            ...s,
            status: 'error',
            error: err instanceof Error ? err.message : 'Could not sign you in.',
          }))
        }
      }
    }

    authenticate()
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [attempt])

  const retry = () => {
    clearSession()
    setAttempt((a) => a + 1)
  }

  return <AuthContext.Provider value={{ ...state, retry }}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider')
  return ctx
}
