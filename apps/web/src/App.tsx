import { Route, Routes } from 'react-router-dom'
import { AdminApp } from './AdminApp'
import { CustomerApp } from './CustomerApp'

export function App() {
  return (
    <Routes>
      <Route path="/admin/*" element={<AdminApp />} />
      <Route path="/*" element={<CustomerApp />} />
    </Routes>
  )
}
