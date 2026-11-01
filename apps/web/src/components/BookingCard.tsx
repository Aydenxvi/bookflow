import { addDays, format } from 'date-fns'
import { Calendar, User } from 'lucide-react'
import { useMemo, useState } from 'react'
import { StatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { ApiError } from '@/lib/api-client'
import type { BookingOut } from '@/lib/api-types'
import { useAvailability, useCancelBooking, useRescheduleBooking } from '@/lib/queries'
import { cn, formatMoney } from '@/lib/utils'

const WINDOW_DAYS = 14

export function BookingCard({ booking, canAct }: { booking: BookingOut; canAct: boolean }) {
  const [cancelOpen, setCancelOpen] = useState(false)
  const [rescheduleOpen, setRescheduleOpen] = useState(false)

  const timezone = booking.business.timezone
  const dateLabel = new Intl.DateTimeFormat(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    timeZone: timezone,
  }).format(new Date(booking.starts_at))
  const timeLabel = new Intl.DateTimeFormat(undefined, {
    hour: 'numeric',
    minute: '2-digit',
    timeZone: timezone,
  }).format(new Date(booking.starts_at))

  return (
    <Card>
      <CardContent className="pt-5">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="font-medium text-charcoal-900">{booking.service.name}</p>
            <p className="mt-0.5 flex items-center gap-1.5 text-xs text-charcoal-500">
              <User className="size-3.5" /> {booking.staff.display_name}
            </p>
            <p className="mt-1.5 flex items-center gap-1.5 text-sm text-charcoal-900">
              <Calendar className="size-3.5" /> {dateLabel} · {timeLabel}
            </p>
          </div>
          <StatusBadge status={booking.status} />
        </div>

        <div className="mt-3 flex items-center justify-between border-t border-charcoal-100 pt-3">
          <span className="text-sm font-semibold text-charcoal-900">
            {formatMoney(booking.price_minor_units_snapshot, booking.currency_snapshot)}
          </span>
          {canAct && (
            <div className="flex gap-2">
              <Button variant="ghost" size="sm" onClick={() => setRescheduleOpen(true)}>
                Reschedule
              </Button>
              <Button
                variant="destructive"
                size="sm"
                onClick={() => setCancelOpen(true)}
              >
                Cancel
              </Button>
            </div>
          )}
        </div>

        {booking.cancel_reason && (
          <p className="mt-2 text-xs text-charcoal-500">Reason: {booking.cancel_reason}</p>
        )}
      </CardContent>

      <CancelDialog booking={booking} open={cancelOpen} onOpenChange={setCancelOpen} />
      <RescheduleDialog booking={booking} open={rescheduleOpen} onOpenChange={setRescheduleOpen} />
    </Card>
  )
}

function CancelDialog({
  booking,
  open,
  onOpenChange,
}: {
  booking: BookingOut
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const cancelBooking = useCancelBooking()

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Cancel this appointment?</DialogTitle>
          <DialogDescription>
            Your {booking.service.name} on{' '}
            {new Intl.DateTimeFormat(undefined, {
              month: 'short',
              day: 'numeric',
              hour: 'numeric',
              minute: '2-digit',
              timeZone: booking.business.timezone,
            }).format(new Date(booking.starts_at))}{' '}
            will be cancelled. This can't be undone.
          </DialogDescription>
        </DialogHeader>
        {cancelBooking.error && (
          <p className="text-sm text-status-cancelled">
            {cancelBooking.error instanceof ApiError
              ? cancelBooking.error.message
              : 'Something went wrong.'}
          </p>
        )}
        <DialogFooter>
          <Button
            variant="destructive"
            onClick={() =>
              cancelBooking.mutate(
                { bookingId: booking.id },
                { onSuccess: () => onOpenChange(false) },
              )
            }
            disabled={cancelBooking.isPending}
          >
            {cancelBooking.isPending ? 'Cancelling…' : 'Yes, cancel it'}
          </Button>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Keep appointment
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function RescheduleDialog({
  booking,
  open,
  onOpenChange,
}: {
  booking: BookingOut
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const rescheduleBooking = useRescheduleBooking()

  const dateFrom = useMemo(() => format(new Date(), 'yyyy-MM-dd'), [])
  const dateTo = useMemo(() => format(addDays(new Date(), WINDOW_DAYS), 'yyyy-MM-dd'), [])

  const { data: availability, isLoading } = useAvailability(
    booking.business.id,
    booking.service.id,
    booking.staff.id,
    dateFrom,
    dateTo,
  )

  const activeDate = selectedDate ?? availability?.find((d) => d.has_availability)?.date ?? null
  const activeDay = availability?.find((d) => d.date === activeDate)
  const timezone = booking.business.timezone

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Reschedule</DialogTitle>
          <DialogDescription>
            Pick a new time for your {booking.service.name} with {booking.staff.display_name}.
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <p className="py-6 text-center text-sm text-charcoal-500">Loading open times…</p>
        ) : (
          <>
            <div className="no-scrollbar flex gap-2 overflow-x-auto pb-1">
              {availability?.map((day) => {
                const dateObj = new Date(`${day.date}T12:00:00`)
                const isActive = day.date === activeDate
                return (
                  <button
                    key={day.date}
                    disabled={!day.has_availability}
                    onClick={() => setSelectedDate(day.date)}
                    className={cn(
                      'flex min-w-[3.25rem] flex-col items-center gap-0.5 rounded-[var(--radius-control)] border px-2 py-2 text-center',
                      isActive
                        ? 'border-sage-500 bg-sage-600 text-ivory'
                        : day.has_availability
                          ? 'border-charcoal-100 bg-white text-charcoal-900'
                          : 'border-charcoal-100 bg-charcoal-50 text-charcoal-300',
                    )}
                  >
                    <span className="text-[0.6rem] font-medium uppercase">{format(dateObj, 'EEE')}</span>
                    <span className="text-sm font-semibold">{format(dateObj, 'd')}</span>
                  </button>
                )
              })}
            </div>

            <div className="mt-4 grid grid-cols-3 gap-2">
              {activeDay?.slots.length ? (
                activeDay.slots.map((slot) => (
                  <button
                    key={slot.starts_at}
                    onClick={() =>
                      rescheduleBooking.mutate(
                        { bookingId: booking.id, body: { new_starts_at: slot.starts_at } },
                        { onSuccess: () => onOpenChange(false) },
                      )
                    }
                    disabled={rescheduleBooking.isPending}
                    className="rounded-[var(--radius-control)] border border-charcoal-100 bg-white px-2 py-2 text-center text-sm font-medium text-charcoal-900 hover:border-sage-400"
                  >
                    {new Intl.DateTimeFormat(undefined, {
                      hour: 'numeric',
                      minute: '2-digit',
                      timeZone: timezone,
                    }).format(new Date(slot.starts_at))}
                  </button>
                ))
              ) : (
                <p className="col-span-3 py-4 text-center text-sm text-charcoal-500">
                  No open times in the next {WINDOW_DAYS} days.
                </p>
              )}
            </div>
          </>
        )}

        {rescheduleBooking.error && (
          <p className="mt-3 text-sm text-status-cancelled">
            {rescheduleBooking.error instanceof ApiError
              ? rescheduleBooking.error.message
              : 'Something went wrong.'}
          </p>
        )}
      </DialogContent>
    </Dialog>
  )
}
