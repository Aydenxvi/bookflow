/**
 * Hand-written TypeScript mirrors of apps/api/app/schemas/*.py.
 * Kept in lockstep manually for now — see NEXT_STEPS.md for the longer-term
 * idea of generating packages/shared types from the OpenAPI schema instead.
 */

export type BookingStatus = 'pending' | 'confirmed' | 'completed' | 'cancelled' | 'no_show'

export interface BusinessHoursOut {
  weekday: number // 0=Mon .. 6=Sun, matches Python's date.weekday()
  start_time: string // "HH:MM"
  end_time: string
}

export interface BusinessOut {
  id: string
  slug: string
  name: string
  description: string | null
  logo_url: string | null
  cover_image_url: string | null
  address: string | null
  contact_phone: string | null
  contact_email: string | null
  timezone: string
  currency: string
  is_demo: boolean
}

export interface BusinessProfileOut extends BusinessOut {
  hours: BusinessHoursOut[]
}

export interface ServiceOut {
  id: string
  name: string
  description: string | null
  category: string | null
  image_url: string | null
  duration_minutes: number
  price_minor_units: number
  currency: string
  is_active: boolean
}

export const ANY_STAFF_SENTINEL = 'any'

export interface StaffOut {
  id: string
  display_name: string
  photo_url: string | null
  specialization: string | null
  bio: string | null
  is_active: boolean
}

export interface SlotOut {
  staff_id: string
  starts_at: string // ISO, UTC
  ends_at: string
}

export interface DayAvailabilityOut {
  date: string // "YYYY-MM-DD"
  has_availability: boolean
  slots: SlotOut[]
}

export interface BookingCreate {
  business_id: string
  service_id: string
  staff_id?: string | null
  starts_at: string // ISO, UTC — must exactly match a slot from availability
  customer_notes?: string | null
}

export interface BookingRescheduleRequest {
  new_starts_at: string
  new_staff_id?: string | null
}

export interface BookingCancelRequest {
  reason?: string | null
}

export interface BookingOut {
  id: string
  status: BookingStatus
  starts_at: string
  ends_at: string
  price_minor_units_snapshot: number
  currency_snapshot: string
  duration_minutes_snapshot: number
  customer_notes: string | null
  cancel_reason: string | null
  is_demo: boolean
  business: BusinessOut
  service: ServiceOut
  staff: StaffOut
}

export interface BookingListOut {
  upcoming: BookingOut[]
  completed: BookingOut[]
  cancelled: BookingOut[]
}

export interface TelegramAuthRequest {
  init_data: string
}

export interface DemoAuthRequest {
  business_slug?: string | null
}

export interface TokenOut {
  access_token: string
  token_type: string
  is_demo: boolean
}
