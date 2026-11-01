import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './api-client'
import type { BookingCancelRequest, BookingCreate, BookingRescheduleRequest } from './api-types'

export function useBusinessProfile(slug: string) {
  return useQuery({
    queryKey: ['business', slug],
    queryFn: () => api.getBusinessProfile(slug),
  })
}

export function useServices(businessId: string | undefined) {
  return useQuery({
    queryKey: ['services', businessId],
    queryFn: () => api.listServices(businessId!),
    enabled: !!businessId,
  })
}

export function useStaff(businessId: string | undefined, serviceId: string | undefined) {
  return useQuery({
    queryKey: ['staff', businessId, serviceId],
    queryFn: () => api.listStaff(businessId!, serviceId),
    enabled: !!businessId && !!serviceId,
  })
}

export function useAvailability(
  businessId: string | undefined,
  serviceId: string | undefined,
  staffId: string | undefined,
  dateFrom: string,
  dateTo: string,
) {
  return useQuery({
    queryKey: ['availability', businessId, serviceId, staffId, dateFrom, dateTo],
    queryFn: () =>
      api.getAvailability(businessId!, { serviceId: serviceId!, staffId, dateFrom, dateTo }),
    enabled: !!businessId && !!serviceId,
  })
}

export function useMyBookings() {
  return useQuery({
    queryKey: ['bookings', 'mine'],
    queryFn: () => api.listMyBookings(),
  })
}

export function useCreateBooking() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ body, idempotencyKey }: { body: BookingCreate; idempotencyKey: string }) =>
      api.createBooking(body, idempotencyKey),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings', 'mine'] })
      queryClient.invalidateQueries({ queryKey: ['availability'] })
    },
  })
}

export function useCancelBooking() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ bookingId, body }: { bookingId: string; body?: BookingCancelRequest }) =>
      api.cancelBooking(bookingId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings', 'mine'] })
    },
  })
}

export function useRescheduleBooking() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ bookingId, body }: { bookingId: string; body: BookingRescheduleRequest }) =>
      api.rescheduleBooking(bookingId, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['bookings', 'mine'] })
      queryClient.invalidateQueries({ queryKey: ['availability'] })
    },
  })
}
