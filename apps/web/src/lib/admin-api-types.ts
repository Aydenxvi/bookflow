/**
 * Hand-written TypeScript mirrors of apps/api/app/schemas/admin.py.
 * Same manual-sync approach as lib/api-types.ts — see that file's note and
 * NEXT_STEPS.md for the longer-term idea of generating these instead.
 */
import type { BookingStatus, BusinessOut, ServiceOut, StaffOut } from './api-types'

export type MembershipRole = 'platform_admin' | 'business_owner' | 'business_manager' | 'staff'

export interface MembershipOut {
  business_id: string
  business_slug: string
  business_name: string
  role: MembershipRole
}

export interface MeOut {
  id: string
  first_name: string
  last_name: string | null
  is_demo: boolean
  is_platform_admin: boolean
  memberships: MembershipOut[]
}

export interface BusinessProfileUpdate {
  name?: string
  description?: string | null
  logo_url?: string | null
  cover_image_url?: string | null
  address?: string | null
  contact_phone?: string | null
  contact_email?: string | null
  timezone?: string
  currency?: string
}

// --- Services ---------------------------------------------------------

export interface ServiceCreate {
  name: string
  description?: string | null
  category?: string | null
  image_url?: string | null
  duration_minutes: number
  price_minor_units: number
  currency: string
}

export interface ServiceUpdate {
  name?: string
  description?: string | null
  category?: string | null
  image_url?: string | null
  duration_minutes?: number
  price_minor_units?: number
  currency?: string
  is_active?: boolean
}

export type AdminServiceOut = ServiceOut

// --- Staff --------------------------------------------------------------

export interface StaffCreate {
  display_name: string
  photo_url?: string | null
  specialization?: string | null
  bio?: string | null
  service_ids: string[]
}

export interface StaffUpdate {
  display_name?: string
  photo_url?: string | null
  specialization?: string | null
  bio?: string | null
  is_active?: boolean
}

export interface StaffServicesUpdate {
  service_ids: string[]
}

export interface AdminStaffOut {
  id: string
  display_name: string
  photo_url: string | null
  specialization: string | null
  bio: string | null
  is_active: boolean
  service_ids: string[]
}

// --- Schedules ------------------------------------------------------------

export interface BreakIn {
  start_time: string // "HH:MM"
  end_time: string
}

export interface DayScheduleIn {
  weekday: number // 0=Mon .. 6=Sun
  start_time: string
  end_time: string
  breaks: BreakIn[]
}

export interface WeeklyScheduleUpdate {
  days: DayScheduleIn[]
}

export interface BreakOut {
  start_time: string
  end_time: string
}

export interface DayScheduleOut {
  weekday: number
  start_time: string
  end_time: string
  breaks: BreakOut[]
}

export type ScheduleExceptionType = 'leave' | 'break' | 'holiday' | 'closure'

export interface ScheduleExceptionCreate {
  staff_id?: string | null
  date: string // "YYYY-MM-DD"
  start_time?: string | null
  end_time?: string | null
  type: ScheduleExceptionType
  note?: string | null
}

export interface ScheduleExceptionOut {
  id: string
  staff_id: string | null
  date: string
  start_time: string | null
  end_time: string | null
  type: ScheduleExceptionType
  note: string | null
}

// --- Booking policy --------------------------------------------------------

export type BookingConfirmationMode = 'automatic' | 'manual'

export interface BookingPolicyOut {
  confirmation_mode: BookingConfirmationMode
  slot_interval_minutes: number
  buffer_minutes: number
  min_lead_time_minutes: number
  max_advance_days: number
  cancellation_window_minutes: number
  reschedule_window_minutes: number
  reminder_offsets_minutes: number[]
}

export interface BookingPolicyUpdate {
  confirmation_mode?: BookingConfirmationMode
  slot_interval_minutes?: number
  buffer_minutes?: number
  min_lead_time_minutes?: number
  max_advance_days?: number
  cancellation_window_minutes?: number
  reschedule_window_minutes?: number
  reminder_offsets_minutes?: number[]
}

// --- Admin bookings / calendar ----------------------------------------

export interface ManualBookingCreate {
  service_id: string
  staff_id?: string | null
  starts_at: string // ISO, UTC
  customer_name: string
  customer_phone?: string | null
  customer_notes?: string | null
}

export interface BookingStatusUpdate {
  status: BookingStatus
  note?: string | null
}

export interface AdminCustomerOut {
  id: string
  display_name: string
  phone: string | null
  is_demo: boolean
}

export interface AdminBookingOut {
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
  service: ServiceOut
  staff: StaffOut
  customer: AdminCustomerOut
}

// --- Dashboard -------------------------------------------------------------

export interface ServiceCountOut {
  service_id: string
  name: string
  count: number
}

export interface StaffCountOut {
  staff_id: string
  display_name: string
  count: number
}

export interface DashboardSummaryOut {
  today_count: number
  upcoming_count: number
  completed_count: number
  cancelled_count: number
  revenue_minor_units: number
  revenue_currency: string
  popular_services: ServiceCountOut[]
  staff_workload: StaffCountOut[]
}

export type { BookingStatus, BusinessOut }
