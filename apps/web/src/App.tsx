import { Route, Routes } from 'react-router-dom'
import { AppShell } from '@/components/layout/AppShell'
import { AuthGate } from '@/components/layout/AuthGate'
import { AppointmentsPage } from '@/pages/AppointmentsPage'
import { ConfirmPage } from '@/pages/ConfirmPage'
import { DateTimePage } from '@/pages/DateTimePage'
import { HomePage } from '@/pages/HomePage'
import { SpecialistPage } from '@/pages/SpecialistPage'
import { SuccessPage } from '@/pages/SuccessPage'

export function App() {
  return (
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
  )
}
