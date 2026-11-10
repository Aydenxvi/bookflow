import { Calendar, Sparkles, X } from 'lucide-react'
import { useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { useAuth } from '@/lib/auth'

const navItems = [
  { to: '/', label: 'Book', icon: Sparkles, end: true },
  { to: '/appointments', label: 'Appointments', icon: Calendar, end: false },
]

// Dismissal is per-browser (localStorage), not a one-time close: a visitor who dismisses it
// once won't see it again on this device, but it still greets anyone new who opens the demo
// without a real Telegram account.
const DISMISS_KEY = 'bookflow-demo-banner-dismissed'

export function AppShell() {
  const { isDemo } = useAuth()
  const [dismissed, setDismissed] = useState(() => {
    try {
      return localStorage.getItem(DISMISS_KEY) === '1'
    } catch {
      return false
    }
  })

  return (
    <div className="mx-auto flex min-h-dvh max-w-md flex-col bg-ivory">
      {isDemo && !dismissed && (
        <div className="relative bg-sage-600 px-4 py-2 pr-9 text-center text-xs font-medium text-ivory">
          Demo mode — exploring as a sample customer of ATELIER. No real Telegram account needed.
          <button
            type="button"
            onClick={() => {
              setDismissed(true)
              try {
                localStorage.setItem(DISMISS_KEY, '1')
              } catch {
                // best-effort only — missing localStorage just means it reappears next visit
              }
            }}
            aria-label="Dismiss"
            className="absolute inset-y-0 right-2 flex items-center text-ivory/80 hover:text-ivory"
          >
            <X className="size-4" />
          </button>
        </div>
      )}
      <main className="flex-1 overflow-y-auto pb-24">
        <Outlet />
      </main>
      <nav
        className="fixed inset-x-0 bottom-0 mx-auto flex max-w-md justify-around border-t border-charcoal-100 bg-ivory/95 px-2 pt-2 backdrop-blur"
        style={{ paddingBottom: 'calc(0.5rem + var(--tg-safe-bottom))' }}
      >
        {navItems.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                'flex flex-1 flex-col items-center gap-1 rounded-xl px-3 py-2 text-xs font-medium transition-colors',
                isActive ? 'text-sage-700' : 'text-charcoal-500',
              )
            }
          >
            <Icon className="size-5" />
            {label}
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
