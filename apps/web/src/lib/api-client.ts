import type {
  BookingCancelRequest,
  BookingCreate,
  BookingListOut,
  BookingOut,
  BookingRescheduleRequest,
  BusinessProfileOut,
  DayAvailabilityOut,
  DemoAuthRequest,
  ServiceOut,
  StaffOut,
  TelegramAuthRequest,
  TokenOut,
} from './api-types'

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

const TOKEN_KEY = 'bookflow.token'
const IS_DEMO_KEY = 'bookflow.isDemo'

export function getStoredToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function getIsDemoSession(): boolean {
  return localStorage.getItem(IS_DEMO_KEY) === '1'
}

export function storeSession(token: string, isDemo: boolean) {
  localStorage.setItem(TOKEN_KEY, token)
  localStorage.setItem(IS_DEMO_KEY, isDemo ? '1' : '0')
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY)
  localStorage.removeItem(IS_DEMO_KEY)
}

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

interface RequestOptions {
  method?: string
  body?: unknown
  auth?: boolean
  idempotencyKey?: string
  query?: Record<string, string | undefined>
}

async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, auth = true, idempotencyKey, query } = opts

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
  if (idempotencyKey) headers['Idempotency-Key'] = idempotencyKey
  if (auth) {
    const token = getStoredToken()
    if (token) headers.Authorization = `Bearer ${token}`
  }

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
        // FastAPI/Pydantic validation error shape
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

export const api = {
  authTelegram: (body: TelegramAuthRequest) =>
    request<TokenOut>('/api/v1/auth/telegram', { method: 'POST', body, auth: false }),

  authDemo: (body: DemoAuthRequest = {}) =>
    request<TokenOut>('/api/v1/auth/demo', { method: 'POST', body, auth: false }),

  getBusinessProfile: (slug: string) =>
    request<BusinessProfileOut>(`/api/v1/businesses/${slug}`),

  listServices: (businessId: string) =>
    request<ServiceOut[]>(`/api/v1/businesses/${businessId}/services`),

  listStaff: (businessId: string, serviceId?: string) =>
    request<StaffOut[]>(`/api/v1/businesses/${businessId}/staff`, {
      query: { service_id: serviceId },
    }),

  getAvailability: (
    businessId: string,
    params: { serviceId: string; staffId?: string; dateFrom: string; dateTo: string },
  ) =>
    request<DayAvailabilityOut[]>(`/api/v1/businesses/${businessId}/availability`, {
      query: {
        service_id: params.serviceId,
        staff_id: params.staffId,
        date_from: params.dateFrom,
        date_to: params.dateTo,
      },
    }),

  createBooking: (body: BookingCreate, idempotencyKey: string) =>
    request<BookingOut>('/api/v1/bookings', { method: 'POST', body, idempotencyKey }),

  listMyBookings: () => request<BookingListOut>('/api/v1/bookings/mine'),

  cancelBooking: (bookingId: string, body: BookingCancelRequest = {}) =>
    request<BookingOut>(`/api/v1/bookings/${bookingId}/cancel`, { method: 'POST', body }),

  rescheduleBooking: (bookingId: string, body: BookingRescheduleRequest) =>
    request<BookingOut>(`/api/v1/bookings/${bookingId}/reschedule`, { method: 'POST', body }),
}
