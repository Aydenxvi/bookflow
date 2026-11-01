import { Calendar, LayoutDashboard, Scissors, Settings, Users } from 'lucide-react'
import { NavLink, Outlet } from 'react-router-dom'
import { cn } from '@/lib/utils'
import { useAdminAuth } from '@/lib/admin-auth'

const navItems = [
  { to: '/admin', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/admin/calendar', label: 'Calendar', icon: Calendar, end: false },
  { to: '/admin/services', label: 'Services', icon: Scissors, end: false },
  { to: '/admin/staff', label: 'Staff', icon: Users, end: false },
  { to: '/admin/settings', label: 'Settings', icon: Settings, end: false },
]

export function AdminShell() {
  const { membership, firstName } = useAdminAuth()

  return (
    <div className="flex min-h-dvh bg-ivory-soft">
      <aside className="flex w-60 shrink-0 flex-col border-r border-charcoal-100 bg-ivory">
        <div className="px-5 py-6">
          <p className="font-display text-lg font-bold text-charcoal-900">BookFlow</p>
          <p className="text-xs text-charcoal-500">{membership?.business_name ?? 'Admin'}</p>
        </div>

        <nav className="flex-1 space-y-1 px-3">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-[var(--radius-control)] px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive ? 'bg-sage-100 text-sage-700' : 'text-charcoal-700 hover:bg-ivory-soft',
                )
              }
            >
              <Icon className="size-4.5" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-charcoal-100 px-5 py-4">
          <p className="text-xs text-charcoal-500">
            Signed in as <span className="font-medium text-charcoal-700">{firstName}</span>
          </p>
          <p className="mt-0.5 text-xs text-charcoal-300 capitalize">{membership?.role.replace('_', ' ')}</p>
        </div>
      </aside>

      <div className="flex-1">
        <div className="bg-sage-600 px-6 py-2 text-center text-xs font-medium text-ivory">
          Demo admin dashboard — exploring {membership?.business_name} as a sample business owner. No real
          account needed.
        </div>
        <main className="p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
