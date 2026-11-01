import { ChevronLeft, User } from 'lucide-react'
import { useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { ApiError } from '@/lib/api-client'
import { ANY_STAFF_SENTINEL } from '@/lib/api-types'
import { DEMO_BUSINESS_SLUG } from '@/lib/config'
import { useBusinessProfile, useCreateBooking, useServices, useStaff } from '@/lib/queries'
import { formatDuration, formatMoney } from '@/lib/utils'

export function ConfirmPage() {
  const { serviceId, staffId } = useParams<{ serviceId: string; staffId: string }>()
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()

  const slotIso = searchParams.get('slot')
  const slotStaffId = searchParams.get('slotStaffId')
  const isAnyStaff = staffId === ANY_STAFF_SENTINEL

  const { data: business } = useBusinessProfile(DEMO_BUSINESS_SLUG)
  const { data: services } = useServices(business?.id)
  const { data: staffList } = useStaff(business?.id, serviceId)
  const service = services?.find((s) => s.id === serviceId)
  const resolvedStaff = staffList?.find((s) => s.id === (slotStaffId ?? staffId))

  const [notes, setNotes] = useState('')
  const [idempotencyKey] = useState(() => crypto.randomUUID())
  const createBooking = useCreateBooking()

  if (!slotIso || !service || !business) {
    return (
      <div className="p-6 text-center text-sm text-charcoal-500">
        Something's missing — go back and pick a time again.
      </div>
    )
  }

  const timezone = business.timezone
  const slotDate = new Date(slotIso)
  const dateLabel = new Intl.DateTimeFormat(undefined, {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    timeZone: timezone,
  }).format(slotDate)
  const timeLabel = new Intl.DateTimeFormat(undefined, {
    hour: 'numeric',
    minute: '2-digit',
    timeZone: timezone,
  }).format(slotDate)

  async function handleConfirm() {
    try {
      const booking = await createBooking.mutateAsync({
        body: {
          business_id: business!.id,
          service_id: service!.id,
          staff_id: isAnyStaff ? null : (slotStaffId ?? staffId!),
          starts_at: slotIso!,
          customer_notes: notes.trim() ? notes.trim() : null,
        },
        idempotencyKey,
      })
      navigate(`/book/success/${booking.id}`)
    } catch {
      // surfaced via createBooking.error below
    }
  }

  const errorMessage =
    createBooking.error instanceof ApiError
      ? createBooking.error.status === 409
        ? 'That time was just taken by another customer. Please pick a different time.'
        : createBooking.error.message
      : createBooking.error
        ? 'Something went wrong. Please try again.'
        : null

  return (
    <div className="p-5">
      <button
        onClick={() => navigate(-1)}
        className="mb-4 flex items-center gap-1 text-sm text-charcoal-500 hover:text-charcoal-900"
      >
        <ChevronLeft className="size-4" /> Back
      </button>

      <h1 className="font-display text-xl font-bold text-charcoal-900">Confirm your booking</h1>

      <Card className="mt-5">
        <CardContent className="pt-5">
          <dl className="space-y-3 text-sm">
            <div className="flex justify-between">
              <dt className="text-charcoal-500">Service</dt>
              <dd className="font-medium text-charcoal-900">{service.name}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-charcoal-500">Specialist</dt>
              <dd className="flex items-center gap-1.5 font-medium text-charcoal-900">
                <User className="size-3.5" /> {resolvedStaff?.display_name ?? 'Assigned specialist'}
              </dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-charcoal-500">Date</dt>
              <dd className="font-medium text-charcoal-900">{dateLabel}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-charcoal-500">Time</dt>
              <dd className="font-medium text-charcoal-900">{timeLabel}</dd>
            </div>
            <div className="flex justify-between">
              <dt className="text-charcoal-500">Duration</dt>
              <dd className="font-medium text-charcoal-900">{formatDuration(service.duration_minutes)}</dd>
            </div>
            <div className="flex justify-between border-t border-charcoal-100 pt-3">
              <dt className="text-charcoal-500">Price</dt>
              <dd className="font-semibold text-charcoal-900">
                {formatMoney(service.price_minor_units, service.currency)}
              </dd>
            </div>
          </dl>
        </CardContent>
      </Card>

      <div className="mt-5">
        <label className="mb-1.5 block text-sm font-medium text-charcoal-900">
          Notes for the business (optional)
        </label>
        <Textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Anything the specialist should know..."
          maxLength={1000}
        />
      </div>

      {errorMessage && (
        <p className="mt-4 rounded-[var(--radius-control)] bg-status-cancelled/10 p-3 text-sm text-status-cancelled">
          {errorMessage}
        </p>
      )}

      <Button
        className="mt-6 w-full"
        variant="accent"
        size="lg"
        onClick={handleConfirm}
        disabled={createBooking.isPending}
      >
        {createBooking.isPending ? 'Confirming…' : 'Confirm booking'}
      </Button>
    </div>
  )
}
