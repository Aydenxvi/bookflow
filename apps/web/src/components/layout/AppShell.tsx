import { Calendar, Sparkles } from 'lucide-react'
import { NavLink, Outlet } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { useAuth } from '@/lib/auth'

const navItems = [
  { to: '/', label: 'Book', icon: Sparkles, end: true },
  { to: '/appointments', label: 'Appointments', icon: Calendar, end: false },
]

export function AppShell() {
  const { isDemo } = useAuth()

  return (
    <div className="mx-auto flex min-h-dvh max-w-md flex-col bg-ivory">
      {isDemo && (
        <div className="bg-sage-600 px-4 py-2 text-center text-xs font-medium text-ivory">
          Demo mode — exploring as a sample customer of ATELIER. No real Telegram account needed.
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
