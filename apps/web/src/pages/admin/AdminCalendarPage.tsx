import { Plus } from 'lucide-react'
import { useMemo, useState, type FormEvent } from 'react'
import { StatusBadge } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import type { AdminBookingOut, BookingStatus, ManualBookingCreate } from '@/lib/admin-api-types'
import { useAdminAuth } from '@/lib/admin-auth'
import {
  useAdminBookings,
  useAdminServices,
  useAdminStaff,
  useChangeBookingStatus,
  useCreateManualBooking,
} from '@/lib/admin-queries'
import { ApiError } from '@/lib/api-client'
import { formatMoney } from '@/lib/utils'

const NEXT_STATUSES: Record<BookingStatus, BookingStatus[]> = {
  pending: ['confirmed', 'cancelled'],
  confirmed: ['completed', 'cancelled', 'no_show'],
  completed: [],
  cancelled: [],
  no_show: [],
}

const STATUS_ACTION_LABEL: Record<BookingStatus, string> = {
  pending: 'Mark pending',
  confirmed: 'Confirm',
  completed: 'Mark completed',
  cancelled: 'Cancel',
  no_show: 'Mark no-show',
}

function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10)
}

export function AdminCalendarPage() {
  const { membership } = useAdminAuth()
  const businessId = membership!.business_id

  const [dateFrom, setDateFrom] = useState(() => isoDate(new Date()))
  const [dateTo, setDateTo] = useState(() => isoDate(new Date(Date.now() + 6 * 86_400_000)))
  const [staffId, setStaffId] = useState('')
  const [serviceId, setServiceId] = useState('')
  const [status, setStatus] = useState('')
  const [creating, setCreating] = useState(false)

  const { data: staffList } = useAdminStaff(businessId)
  const { data: services } = useAdminServices(businessId)
  const { data: bookings, isLoading, isError } = useAdminBookings(businessId, {
    dateFrom,
    dateTo,
    staffId: staffId || undefined,
    serviceId: serviceId || undefined,
    status: status || undefined,
  })
  const changeStatus = useChangeBookingStatus(businessId)

  const sorted = useMemo(
    () => [...(bookings ?? [])].sort((a, b) => a.starts_at.localeCompare(b.starts_at)),
    [bookings],
  )

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-charcoal-900">Calendar</h1>
          <p className="mt-1 text-sm text-charcoal-500">Appointments for {membership?.business_name}.</p>
        </div>
        <Button onClick={() => setCreating(true)}>
          <Plus /> New booking
        </Button>
      </div>

      <Card className="mt-6">
        <CardContent className="grid grid-cols-2 gap-3 pt-5 sm:grid-cols-5">
          <div className="space-y-1.5">
            <Label htmlFor="cal-from">From</Label>
            <Input id="cal-from" type="date" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="cal-to">To</Label>
            <Input id="cal-to" type="date" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="cal-staff">Staff</Label>
            <Select id="cal-staff" value={staffId} onChange={(e) => setStaffId(e.target.value)}>
              <option value="">Everyone</option>
              {(staffList ?? []).map((s) => (
                <option key={s.id} value={s.id}>
                  {s.display_name}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="cal-service">Service</Label>
            <Select id="cal-service" value={serviceId} onChange={(e) => setServiceId(e.target.value)}>
              <option value="">All services</option>
              {(services ?? []).map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="cal-status">Status</Label>
            <Select id="cal-status" value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">Any status</option>
              <option value="pending">Pending</option>
              <option value="confirmed">Confirmed</option>
              <option value="completed">Completed</option>
              <option value="cancelled">Cancelled</option>
              <option value="no_show">No-show</option>
            </Select>
          </div>
        </CardContent>
      </Card>

      {isError && (
        <p className="mt-6 text-sm text-charcoal-500">Couldn't load bookings. Please try again shortly.</p>
      )}

      {isLoading ? (
        <div className="mt-6 space-y-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      ) : (
        <div className="mt-6 space-y-2.5">
          {sorted.length === 0 && <p className="text-sm text-charcoal-500">No bookings in this range.</p>}
          {sorted.map((booking) => (
            <BookingRow
              key={booking.id}
              booking={booking}
              onChangeStatus={(next) =>
                changeStatus.mutate({ bookingId: booking.id, body: { status: next } })
              }
              pending={changeStatus.isPending}
            />
          ))}
        </div>
      )}

      {creating && (
        <NewBookingDialog
          businessId={businessId}
          services={services ?? []}
          staffList={staffList ?? []}
          onClose={() => setCreating(false)}
        />
      )}
    </div>
  )
}

function BookingRow({
  booking,
  onChangeStatus,
  pending,
}: {
  booking: AdminBookingOut
  onChangeStatus: (next: BookingStatus) => void
  pending: boolean
}) {
  const start = new Date(booking.starts_at)
  const dateLabel = new Intl.DateTimeFormat(undefined, { weekday: 'short', month: 'short', day: 'numeric' }).format(
    start,
  )
  const timeLabel = new Intl.DateTimeFormat(undefined, { hour: 'numeric', minute: '2-digit' }).format(start)

  return (
    <Card>
      <CardContent className="flex flex-wrap items-center justify-between gap-3 pt-5">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <p className="font-medium text-charcoal-900">
              {dateLabel} · {timeLabel}
            </p>
            <StatusBadge status={booking.status} />
          </div>
          <p className="mt-1 text-sm text-charcoal-700">
            {booking.service.name} with {booking.staff.display_name}
          </p>
          <p className="text-xs text-charcoal-500">
            {booking.customer.display_name}
            {booking.customer.phone ? ` · ${booking.customer.phone}` : ''} ·{' '}
            {formatMoney(booking.price_minor_units_snapshot, booking.currency_snapshot)}
          </p>
        </div>
        <div className="flex shrink-0 flex-wrap gap-2">
          {NEXT_STATUSES[booking.status].map((next) => (
            <Button
              key={next}
              size="sm"
              variant={next === 'cancelled' ? 'destructive' : 'outline'}
              disabled={pending}
              onClick={() => onChangeStatus(next)}
            >
              {STATUS_ACTION_LABEL[next]}
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

function NewBookingDialog({
  businessId,
  services,
  staffList,
  onClose,
}: {
  businessId: string
  services: { id: string; name: string }[]
  staffList: { id: string; display_name: string }[]
  onClose: () => void
}) {
  const createBooking = useCreateManualBooking(businessId)

  const [serviceId, setServiceId] = useState(services[0]?.id ?? '')
  const [staffId, setStaffId] = useState('')
  const [startsAt, setStartsAt] = useState('')
  const [customerName, setCustomerName] = useState('')
  const [customerPhone, setCustomerPhone] = useState('')
  const [notes, setNotes] = useState('')

  const errorMessage =
    createBooking.error instanceof ApiError
      ? createBooking.error.status === 409
        ? 'That staff member already has a booking at that time.'
        : createBooking.error.message
      : createBooking.error
        ? 'Something went wrong.'
        : null

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const body: ManualBookingCreate = {
      service_id: serviceId,
      staff_id: staffId || null,
      starts_at: new Date(startsAt).toISOString(),
      customer_name: customerName,
      customer_phone: customerPhone.trim() || null,
      customer_notes: notes.trim() || null,
    }
    try {
      await createBooking.mutateAsync(body)
      onClose()
    } catch {
      // surfaced via errorMessage above
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New manual booking</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="mb-service">Service</Label>
            <Select id="mb-service" value={serviceId} onChange={(e) => setServiceId(e.target.value)} required>
              {services.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="mb-staff">Staff</Label>
            <Select id="mb-staff" value={staffId} onChange={(e) => setStaffId(e.target.value)}>
              <option value="">Any available</option>
              {staffList.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.display_name}
                </option>
              ))}
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="mb-starts">Date &amp; time</Label>
            <Input
              id="mb-starts"
              type="datetime-local"
              value={startsAt}
              onChange={(e) => setStartsAt(e.target.value)}
              required
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="mb-name">Customer name</Label>
            <Input
              id="mb-name"
              value={customerName}
              onChange={(e) => setCustomerName(e.target.value)}
              required
              maxLength={160}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="mb-phone">Customer phone (optional)</Label>
            <Input id="mb-phone" value={customerPhone} onChange={(e) => setCustomerPhone(e.target.value)} />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="mb-notes">Notes (optional)</Label>
            <Textarea id="mb-notes" value={notes} onChange={(e) => setNotes(e.target.value)} maxLength={1000} />
          </div>

          {errorMessage && (
            <p className="rounded-[var(--radius-control)] bg-status-cancelled/10 p-3 text-sm text-status-cancelled">
              {errorMessage}
            </p>
          )}

          <DialogFooter>
            <Button type="submit" disabled={createBooking.isPending || !serviceId}>
              {createBooking.isPending ? 'Creating…' : 'Create booking'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
