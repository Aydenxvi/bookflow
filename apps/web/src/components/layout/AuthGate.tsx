import type { ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/lib/auth'

/** Blocks rendering the app until a BookFlow session token is resolved
 * (real Telegram auth or the browser demo-mode fallback — see lib/auth.tsx). */
export function AuthGate({ children }: { children: ReactNode }) {
  const { status, error, retry } = useAuth()

  if (status === 'loading') {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-ivory">
        <div className="flex flex-col items-center gap-3">
          <div className="size-8 animate-spin rounded-full border-2 border-sage-200 border-t-sage-600" />
          <p className="text-sm text-charcoal-500">Loading BookFlow…</p>
        </div>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="flex min-h-dvh flex-col items-center justify-center gap-4 bg-ivory p-6 text-center">
        <p className="font-medium text-charcoal-900">Couldn't sign you in</p>
        <p className="text-sm text-charcoal-500">{error}</p>
        <Button onClick={retry}>Try again</Button>
      </div>
    )
  }

  return <>{children}</>
}
