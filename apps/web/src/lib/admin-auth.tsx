import { createContext, useContext, useEffect, useState, type ReactNode } from 'react'
import { adminApi, clearAdminSession, getAdminToken, storeAdminToken } from './admin-api-client'
import { DEMO_BUSINESS_SLUG } from './config'
import type { MembershipOut } from './admin-api-types'

interface AdminAuthState {
  status: 'loading' | 'ready' | 'error'
  membership: MembershipOut | null
  firstName: string | null
  error: string | null
  retry: () => void
}

const AdminAuthContext = createContext<AdminAuthState | null>(null)

/**
 * Resolves an admin session before the admin dashboard renders anything:
 * a browser demo-mode sign-in (spec section 19 — "a sample admin dashboard,
 * explorable without a real Telegram account or a real business-owner
 * relationship"), mirroring how lib/auth.tsx handles the customer side.
 *
 * A fresh synthetic owner is created on first visit (via /auth/demo-admin)
 * and reused from localStorage afterward. /auth/me then resolves which
 * business and role this session can administer, rather than trusting
 * anything client-stored for that.
 */
export function AdminAuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<Omit<AdminAuthState, 'retry'>>({
    status: 'loading',
    membership: null,
    firstName: null,
    error: null,
  })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false

    async function authenticate() {
      setState((s) => ({ ...s, status: 'loading', error: null }))

      try {
        if (!getAdminToken()) {
          const token = await adminApi.authDemoAdmin({ business_slug: DEMO_BUSINESS_SLUG })
          storeAdminToken(token.access_token)
        }

        const me = await adminApi.getMe()
        const membership =
          me.memberships.find((m) => m.business_slug === DEMO_BUSINESS_SLUG) ?? me.memberships[0] ?? null

        if (!membership) {
          throw new Error('This account has no business to administer yet.')
        }

        if (!cancelled) {
          setState({ status: 'ready', membership, firstName: me.first_name, error: null })
        }
      } catch (err) {
        // A stored token might be stale/invalid (e.g. from an earlier session
        // that's since been cleared server-side) — drop it and show a retry
        // rather than looping on the same bad token.
        clearAdminSession()
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
    clearAdminSession()
    setAttempt((a) => a + 1)
  }

  return <AdminAuthContext.Provider value={{ ...state, retry }}>{children}</AdminAuthContext.Provider>
}

export function useAdminAuth(): AdminAuthState {
  const ctx = useContext(AdminAuthContext)
  if (!ctx) throw new Error('useAdminAuth must be used within an AdminAuthProvider')
  return ctx
}
