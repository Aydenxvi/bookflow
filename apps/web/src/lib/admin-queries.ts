import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { adminApi } from './admin-api-client'
import type {
  BookingPolicyUpdate,
  BookingStatusUpdate,
  BusinessProfileUpdate,
  ManualBookingCreate,
  ScheduleExceptionCreate,
  ServiceCreate,
  ServiceUpdate,
  StaffCreate,
  StaffServicesUpdate,
  StaffUpdate,
  WeeklyScheduleUpdate,
} from './admin-api-types'

// --- Dashboard ---

export function useAdminDashboard(businessId: string | undefined) {
  return useQuery({
    queryKey: ['admin', 'dashboard', businessId],
    queryFn: () => adminApi.getDashboard(businessId!),
    enabled: !!businessId,
  })
}

export function useDashboardAnalytics(businessId: string | undefined, days = 30) {
  return useQuery({
    queryKey: ['admin', 'dashboard-analytics', businessId, days],
    queryFn: () => adminApi.getDashboardAnalytics(businessId!, days),
    enabled: !!businessId,
  })
}

// --- Services ---

export function useAdminServices(businessId: string | undefined) {
  return useQuery({
    queryKey: ['admin', 'services', businessId],
    queryFn: () => adminApi.listServices(businessId!),
    enabled: !!businessId,
  })
}

export function useCreateService(businessId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: ServiceCreate) => adminApi.createService(businessId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'services', businessId] }),
  })
}

export function useUpdateService(businessId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ serviceId, body }: { serviceId: string; body: ServiceUpdate }) =>
      adminApi.updateService(businessId, serviceId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'services', businessId] }),
  })
}

export function useSetServiceArchived(businessId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ serviceId, archived }: { serviceId: string; archived: boolean }) =>
      archived ? adminApi.archiveService(businessId, serviceId) : adminApi.unarchiveService(businessId, serviceId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'services', businessId] }),
  })
}

// --- Staff ---

export function useAdminStaff(businessId: string | undefined) {
  return useQuery({
    queryKey: ['admin', 'staff', businessId],
    queryFn: () => adminApi.listStaff(businessId!),
    enabled: !!businessId,
  })
}

export function useCreateStaff(businessId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: StaffCreate) => adminApi.createStaff(businessId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'staff', businessId] }),
  })
}

export function useUpdateStaff(businessId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ staffId, body }: { staffId: string; body: StaffUpdate }) =>
      adminApi.updateStaff(businessId, staffId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'staff', businessId] }),
  })
}

export function useSetStaffServices(businessId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ staffId, body }: { staffId: string; body: StaffServicesUpdate }) =>
      adminApi.setStaffServices(businessId, staffId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'staff', businessId] }),
  })
}

export function useStaffSchedule(businessId: string | undefined, staffId: string | undefined) {
  return useQuery({
    queryKey: ['admin', 'staff-schedule', businessId, staffId],
    queryFn: () => adminApi.getStaffSchedule(businessId!, staffId!),
    enabled: !!businessId && !!staffId,
  })
}

export function useSetStaffSchedule(businessId: string, staffId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: WeeklyScheduleUpdate) => adminApi.setStaffSchedule(businessId, staffId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'staff-schedule', businessId, staffId] }),
  })
}

export function useExceptions(businessId: string | undefined) {
  return useQuery({
    queryKey: ['admin', 'exceptions', businessId],
    queryFn: () => adminApi.listExceptions(businessId!),
    enabled: !!businessId,
  })
}

export function useCreateException(businessId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: ScheduleExceptionCreate) => adminApi.createException(businessId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'exceptions', businessId] }),
  })
}

export function useDeleteException(businessId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (exceptionId: string) => adminApi.deleteException(businessId, exceptionId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'exceptions', businessId] }),
  })
}

// --- Business profile / hours / policy ---

export function useAdminProfile(businessId: string | undefined) {
  return useQuery({
    queryKey: ['admin', 'profile', businessId],
    queryFn: () => adminApi.getProfile(businessId!),
    enabled: !!businessId,
  })
}

export function useUpdateProfile(businessId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: BusinessProfileUpdate) => adminApi.updateProfile(businessId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'profile', businessId] }),
  })
}

export function useBusinessHours(businessId: string | undefined) {
  return useQuery({
    queryKey: ['admin', 'hours', businessId],
    queryFn: () => adminApi.getHours(businessId!),
    enabled: !!businessId,
  })
}

export function useSetBusinessHours(businessId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: WeeklyScheduleUpdate) => adminApi.setHours(businessId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'hours', businessId] }),
  })
}

export function useBookingPolicy(businessId: string | undefined) {
  return useQuery({
    queryKey: ['admin', 'policy', businessId],
    queryFn: () => adminApi.getPolicy(businessId!),
    enabled: !!businessId,
  })
}

export function useUpdateBookingPolicy(businessId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: BookingPolicyUpdate) => adminApi.updatePolicy(businessId, body),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['admin', 'policy', businessId] }),
  })
}

// --- Bookings / calendar ---

export function useAdminBookings(
  businessId: string | undefined,
  params: { dateFrom: string; dateTo: string; staffId?: string; serviceId?: string; status?: string },
) {
  return useQuery({
    queryKey: ['admin', 'bookings', businessId, params],
    queryFn: () => adminApi.listBookings(businessId!, params),
    enabled: !!businessId,
  })
}

export function useCreateManualBooking(businessId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (body: ManualBookingCreate) => adminApi.createManualBooking(businessId, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['admin', 'bookings', businessId] })
      qc.invalidateQueries({ queryKey: ['admin', 'dashboard', businessId] })
    },
  })
}

export function useChangeBookingStatus(businessId: string) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: ({ bookingId, body }: { bookingId: string; body: BookingStatusUpdate }) =>
      adminApi.changeBookingStatus(businessId, bookingId, body),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: ['admin', 'bookings', businessId] })
      qc.invalidateQueries({ queryKey: ['admin', 'dashboard', businessId] })
      qc.invalidateQueries({ queryKey: ['admin', 'booking-history', businessId, variables.bookingId] })
    },
  })
}

export function useBookingHistory(businessId: string | undefined, bookingId: string | undefined) {
  return useQuery({
    queryKey: ['admin', 'booking-history', businessId, bookingId],
    queryFn: () => adminApi.getBookingHistory(businessId!, bookingId!),
    enabled: !!businessId && !!bookingId,
  })
}
