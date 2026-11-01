import { Route, Routes } from 'react-router-dom'
import { AdminAuthGate } from '@/components/layout/AdminAuthGate'
import { AdminShell } from '@/components/layout/AdminShell'
import { AdminAuthProvider } from '@/lib/admin-auth'
import { AdminAnalyticsPage } from '@/pages/admin/AdminAnalyticsPage'
import { AdminCalendarPage } from '@/pages/admin/AdminCalendarPage'
import { AdminDashboardPage } from '@/pages/admin/AdminDashboardPage'
import { AdminServicesPage } from '@/pages/admin/AdminServicesPage'
import { AdminSettingsPage } from '@/pages/admin/AdminSettingsPage'
import { AdminStaffPage } from '@/pages/admin/AdminStaffPage'

/** The business-owner/manager/staff admin dashboard, mounted at /admin/*.
 * Spec section 19: explorable without a real Telegram account or a real
 * business-owner relationship — see lib/admin-auth.tsx for the demo sign-in. */
export function AdminApp() {
  return (
    <AdminAuthProvider>
      <AdminAuthGate>
        <Routes>
          <Route element={<AdminShell />}>
            <Route index element={<AdminDashboardPage />} />
            <Route path="calendar" element={<AdminCalendarPage />} />
            <Route path="analytics" element={<AdminAnalyticsPage />} />
            <Route path="services" element={<AdminServicesPage />} />
            <Route path="staff" element={<AdminStaffPage />} />
            <Route path="settings" element={<AdminSettingsPage />} />
          </Route>
        </Routes>
      </AdminAuthGate>
    </AdminAuthProvider>
  )
}
