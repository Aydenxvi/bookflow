import type { DemoAuthRequest, TokenOut } from './api-types'
import { API_BASE_URL, ApiError } from './api-client'
import type {
  AdminBookingOut,
  AdminStaffOut,
  BookingPolicyOut,
  BookingPolicyUpdate,
  BookingStatusUpdate,
  BusinessOut,
  BusinessProfileUpdate,
  DayScheduleOut,
  ManualBookingCreate,
  MeOut,
  ScheduleExceptionCreate,
  ScheduleExceptionOut,
  AdminServiceOut,
  ServiceCreate,
  ServiceUpdate,
  StaffCreate,
  StaffServicesUpdate,
  StaffUpdate,
  WeeklyScheduleUpdate,
  DashboardSummaryOut,
} from './admin-api-types'

// Deliberately separate storage keys from the customer session (lib/api-client.ts)
// so a browser can hold a customer demo session and an admin demo session at
// the same time without clobbering each other.
const ADMIN_TOKEN_KEY = 'bookflow.admin.token'

export function getAdminToken(): string | null {
  return localStorage.getItem(ADMIN_TOKEN_KEY)
}

export function storeAdminToken(token: string) {
  localStorage.setItem(ADMIN_TOKEN_KEY, token)
}

export function clearAdminSession() {
  localStorage.removeItem(ADMIN_TOKEN_KEY)
}

interface RequestOptions {
  method?: string
  body?: unknown
  query?: Record<string, string | undefined>
}

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, query } = opts

  let url = `${API_BASE_URL}${path}`
  if (query) {
    const params = new URLSearchParams()
    for (const [k, v] of Object.entries(query)) {
      if (v !== undefined) params.set(k, v)
    }
    const qs = params.toString()
    if (qs) url += `?${qs}`
  }

  const headers: Record<string, string> = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  const token = getAdminToken()
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(url, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (!res.ok) {
    let message = res.statusText
    try {
      const data = await res.json()
      if (typeof data?.detail === 'string') message = data.detail
      else if (Array.isArray(data?.detail)) {
        message = data.detail.map((d: { msg?: string }) => d.msg).join('; ')
      }
    } catch {
      // response body wasn't JSON — fall back to statusText
    }
    throw new ApiError(res.status, message)
  }

  if (res.status === 204) return undefined as T
  return (await res.json()) as T
}

export const adminApi = {
  authDemoAdmin: (body: DemoAuthRequest = {}) =>
    request<TokenOut>('/api/v1/auth/demo-admin', { method: 'POST', body }),

  getMe: () => request<MeOut>('/api/v1/auth/me'),

  // --- Services ---
  listServices: (businessId: string) =>
    request<AdminServiceOut[]>(`/api/v1/admin/businesses/${businessId}/services`),
  createService: (businessId: string, body: ServiceCreate) =>
    request<AdminServiceOut>(`/api/v1/admin/businesses/${businessId}/services`, { method: 'POST', body }),
  updateService: (businessId: string, serviceId: string, body: ServiceUpdate) =>
    request<AdminServiceOut>(`/api/v1/admin/businesses/${businessId}/services/${serviceId}`, {
      method: 'PATCH',
      body,
    }),
  archiveService: (businessId: string, serviceId: string) =>
    request<AdminServiceOut>(`/api/v1/admin/businesses/${businessId}/services/${serviceId}/archive`, {
      method: 'POST',
    }),
  unarchiveService: (businessId: string, serviceId: string) =>
    request<AdminServiceOut>(`/api/v1/admin/businesses/${businessId}/services/${serviceId}/unarchive`, {
      method: 'POST',
    }),

  // --- Staff ---
  listStaff: (businessId: string) => request<AdminStaffOut[]>(`/api/v1/admin/businesses/${businessId}/staff`),
  createStaff: (businessId: string, body: StaffCreate) =>
    request<AdminStaffOut>(`/api/v1/admin/businesses/${businessId}/staff`, { method: 'POST', body }),
  updateStaff: (businessId: string, staffId: string, body: StaffUpdate) =>
    request<AdminStaffOut>(`/api/v1/admin/businesses/${businessId}/staff/${staffId}`, {
      method: 'PATCH',
      body,
    }),
  setStaffServices: (businessId: string, staffId: string, body: StaffServicesUpdate) =>
    request<AdminStaffOut>(`/api/v1/admin/businesses/${businessId}/staff/${staffId}/services`, {
      method: 'PUT',
      body,
    }),
  getStaffSchedule: (businessId: string, staffId: string) =>
    request<DayScheduleOut[]>(`/api/v1/admin/businesses/${businessId}/staff/${staffId}/schedule`),
  setStaffSchedule: (businessId: string, staffId: string, body: WeeklyScheduleUpdate) =>
    request<DayScheduleOut[]>(`/api/v1/admin/businesses/${businessId}/staff/${staffId}/schedule`, {
      method: 'PUT',
      body,
    }),
  listExceptions: (businessId: string) =>
    request<ScheduleExceptionOut[]>(`/api/v1/admin/businesses/${businessId}/staff/exceptions`),
  createException: (businessId: string, body: ScheduleExceptionCreate) =>
    request<ScheduleExceptionOut>(`/api/v1/admin/businesses/${businessId}/staff/exceptions`, {
      method: 'POST',
      body,
    }),
  deleteException: (businessId: string, exceptionId: string) =>
    request<void>(`/api/v1/admin/businesses/${businessId}/staff/exceptions/${exceptionId}`, {
      method: 'DELETE',
    }),

  // --- Business profile / hours / policy ---
  getProfile: (businessId: string) => request<BusinessOut>(`/api/v1/admin/businesses/${businessId}/profile`),
  updateProfile: (businessId: string, body: BusinessProfileUpdate) =>
    request<BusinessOut>(`/api/v1/admin/businesses/${businessId}/profile`, { method: 'PATCH', body }),
  getHours: (businessId: string) => request<DayScheduleOut[]>(`/api/v1/admin/businesses/${businessId}/hours`),
  setHours: (businessId: string, body: WeeklyScheduleUpdate) =>
    request<DayScheduleOut[]>(`/api/v1/admin/businesses/${businessId}/hours`, { method: 'PUT', body }),
  getPolicy: (businessId: string) =>
    request<BookingPolicyOut>(`/api/v1/admin/businesses/${businessId}/policy`),
  updatePolicy: (businessId: string, body: BookingPolicyUpdate) =>
    request<BookingPolicyOut>(`/api/v1/admin/businesses/${businessId}/policy`, { method: 'PATCH', body }),

  // --- Bookings / calendar ---
  listBookings: (
    businessId: string,
    params: { dateFrom: string; dateTo: string; staffId?: string; serviceId?: string; status?: string },
  ) =>
    request<AdminBookingOut[]>(`/api/v1/admin/businesses/${businessId}/bookings`, {
      query: {
        date_from: params.dateFrom,
        date_to: params.dateTo,
        staff_id: params.staffId,
        service_id: params.serviceId,
        status: params.status,
      },
    }),
  createManualBooking: (businessId: string, body: ManualBookingCreate) =>
    request<AdminBookingOut>(`/api/v1/admin/businesses/${businessId}/bookings`, { method: 'POST', body }),
  changeBookingStatus: (businessId: string, bookingId: string, body: BookingStatusUpdate) =>
    request<AdminBookingOut>(`/api/v1/admin/businesses/${businessId}/bookings/${bookingId}/status`, {
      method: 'POST',
      body,
    }),

  // --- Dashboard ---
  getDashboard: (businessId: string) =>
    request<DashboardSummaryOut>(`/api/v1/admin/businesses/${businessId}/dashboard`),
}
