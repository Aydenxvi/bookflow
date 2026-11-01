import type { ReactNode } from 'react'
import { Button } from '@/components/ui/button'
import { useAdminAuth } from '@/lib/admin-auth'

/** Blocks rendering the admin dashboard until a demo-admin session token and
 * its business/role membership are resolved — see lib/admin-auth.tsx. */
export function AdminAuthGate({ children }: { children: ReactNode }) {
  const { status, error, retry } = useAdminAuth()

  if (status === 'loading') {
    return (
      <div className="flex min-h-dvh items-center justify-center bg-ivory-soft">
        <div className="flex flex-col items-center gap-3">
          <div className="size-8 animate-spin rounded-full border-2 border-sage-200 border-t-sage-600" />
          <p className="text-sm text-charcoal-500">Signing you in to the dashboard…</p>
        </div>
      </div>
    )
  }

  if (status === 'error') {
    return (
      <div className="flex min-h-dvh flex-col items-center justify-center gap-4 bg-ivory-soft p-6 text-center">
        <p className="font-medium text-charcoal-900">Couldn't open the admin dashboard</p>
        <p className="max-w-sm text-sm text-charcoal-500">{error}</p>
        <Button onClick={retry}>Try again</Button>
      </div>
    )
  }

  return <>{children}</>
}
