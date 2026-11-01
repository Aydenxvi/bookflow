import { Route, Routes } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { AuthGate } from '@/components/layout/AuthGate'
import { AuthProvider } from '@/lib/auth'
import { AppointmentsPage } from '@/pages/AppointmentsPage'
import { ConfirmPage } from '@/pages/ConfirmPage'
import { DateTimePage } from '@/pages/DateTimePage'
import { HomePage } from '@/pages/HomePage'
import { SpecialistPage } from '@/pages/SpecialistPage'
import { SuccessPage } from '@/pages/SuccessPage'

/** The customer-facing Telegram Mini App / browser-demo booking flow —
 * everything outside /admin/*. Its own auth context (lib/auth.tsx) so it
 * never shares a session with the admin dashboard (lib/admin-auth.tsx). */
export function CustomerApp() {
  return (
    <AuthProvider>
      <AuthGate>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<HomePage />} />
            <Route path="book/:serviceId" element={<SpecialistPage />} />
            <Route path="book/:serviceId/:staffId" element={<DateTimePage />} />
            <Route path="book/:serviceId/:staffId/confirm" element={<ConfirmPage />} />
            <Route path="book/success/:bookingId" element={<SuccessPage />} />
            <Route path="appointments" element={<AppointmentsPage />} />
          </Route>
        </Routes>
      </AuthGate>
    </AuthProvider>
  )
}
