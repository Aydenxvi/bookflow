import { CheckCircle2 } from 'lucide-react'
import { useEffect } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { useMyBookings } from '@/lib/queries'
import { formatMoney } from '@/lib/utils'

export function SuccessPage() {
  const { bookingId } = useParams<{ bookingId: string }>()
  const navigate = useNavigate()
  const { data } = useMyBookings()

  const booking = [...(data?.upcoming ?? []), ...(data?.completed ?? [])].find(
    (b) => b.id === bookingId,
  )

  useEffect(() => {
    if (window.Telegram?.WebApp?.HapticFeedback) {
      window.Telegram.WebApp.HapticFeedback.notificationOccurred('success')
    }
  }, [])

  return (
    <div className="flex flex-col items-center p-6 pt-16 text-center">
      <div className="flex size-16 items-center justify-center rounded-full bg-sage-100 text-sage-600">
        <CheckCircle2 className="size-9" />
      </div>
      <h1 className="font-display mt-5 text-2xl font-bold text-charcoal-900">You're all set</h1>
      <p className="mt-2 text-sm text-charcoal-500">
        Your appointment has been booked. We'll notify you before it's time.
      </p>

      {booking && (
        <Card className="mt-6 w-full text-left">
          <CardContent className="pt-5">
            <p className="font-medium text-charcoal-900">{booking.service.name}</p>
            <p className="mt-1 text-sm text-charcoal-500">with {booking.staff.display_name}</p>
            <p className="mt-3 text-sm text-charcoal-900">
              {new Intl.DateTimeFormat(undefined, {
                weekday: 'short',
                month: 'short',
                day: 'numeric',
                hour: 'numeric',
                minute: '2-digit',
                timeZone: booking.business.timezone,
              }).format(new Date(booking.starts_at))}
            </p>
            <p className="mt-1 text-sm font-semibold text-charcoal-900">
              {formatMoney(booking.price_minor_units_snapshot, booking.currency_snapshot)}
            </p>
          </CardContent>
        </Card>
      )}

      <div className="mt-8 flex w-full flex-col gap-2.5">
        <Button variant="accent" size="lg" onClick={() => navigate('/appointments')}>
          View my appointments
        </Button>
        <Button variant="outline" size="lg" onClick={() => navigate('/')}>
          Book something else
        </Button>
      </div>
    </div>
  )
}
