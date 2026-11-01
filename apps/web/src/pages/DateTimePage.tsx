import { addDays, format } from 'date-fns'
import { ChevronLeft } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Skeleton } from '@/components/ui/skeleton'
import { ANY_STAFF_SENTINEL } from '@/lib/api-types'
import { DEMO_BUSINESS_SLUG } from '@/lib/config'
import { useAvailability, useBusinessProfile, useServices, useStaff } from '@/lib/queries'
import { cn, formatDuration } from '@/lib/utils'

const WINDOW_DAYS = 14

export function DateTimePage() {
  const { serviceId, staffId } = useParams<{ serviceId: string; staffId: string }>()
  const navigate = useNavigate()
  const isAnyStaff = staffId === ANY_STAFF_SENTINEL

  const { data: business } = useBusinessProfile(DEMO_BUSINESS_SLUG)
  const { data: services } = useServices(business?.id)
  const { data: staffList } = useStaff(business?.id, serviceId)
  const service = services?.find((s) => s.id === serviceId)
  const staffMember = staffList?.find((s) => s.id === staffId)

  const dateFrom = useMemo(() => format(new Date(), 'yyyy-MM-dd'), [])
  const dateTo = useMemo(() => format(addDays(new Date(), WINDOW_DAYS), 'yyyy-MM-dd'), [])

  const { data: availability, isLoading } = useAvailability(
    business?.id,
    serviceId,
    isAnyStaff ? undefined : staffId,
    dateFrom,
    dateTo,
  )

  const [selectedDate, setSelectedDate] = useState<string | null>(null)
  const activeDate = selectedDate ?? availability?.find((d) => d.has_availability)?.date ?? null
  const activeDay = availability?.find((d) => d.date === activeDate)

  const timezone = business?.timezone ?? 'UTC'

  return (
    <div className="p-5">
      <button
        onClick={() => navigate(`/book/${serviceId}`)}
        className="mb-4 flex items-center gap-1 text-sm text-charcoal-500 hover:text-charcoal-900"
      >
        <ChevronLeft className="size-4" /> Back
      </button>

      <h1 className="font-display text-xl font-bold text-charcoal-900">Pick a date & time</h1>
      <p className="mt-1 text-sm text-charcoal-500">
        {service?.name}
        {service && ` · ${formatDuration(service.duration_minutes)}`}
        {!isAnyStaff && staffMember && ` · with ${staffMember.display_name}`}
        {isAnyStaff && ' · any available specialist'}
      </p>

      {isLoading ? (
        <div className="mt-6 space-y-3">
          <Skeleton className="h-12 w-full" />
          <Skeleton className="h-40 w-full" />
        </div>
      ) : (
        <>
          <div className="no-scrollbar mt-6 flex gap-2 overflow-x-auto pb-1">
            {availability?.map((day) => {
              const dateObj = new Date(`${day.date}T12:00:00`)
              const isActive = day.date === activeDate
              return (
                <button
                  key={day.date}
                  disabled={!day.has_availability}
                  onClick={() => setSelectedDate(day.date)}
                  className={cn(
                    'flex min-w-[3.75rem] flex-col items-center gap-0.5 rounded-[var(--radius-control)] border px-2 py-2.5 text-center transition-colors',
                    isActive
                      ? 'border-sage-500 bg-sage-600 text-ivory'
                      : day.has_availability
                        ? 'border-charcoal-100 bg-white text-charcoal-900 hover:border-sage-300'
                        : 'border-charcoal-100 bg-charcoal-50 text-charcoal-300',
                  )}
                >
                  <span className="text-[0.65rem] font-medium uppercase">{format(dateObj, 'EEE')}</span>
                  <span className="text-base font-semibold">{format(dateObj, 'd')}</span>
                </button>
              )
            })}
          </div>

          <div className="mt-5">
            {activeDay && activeDay.slots.length > 0 ? (
              <div className="grid grid-cols-3 gap-2.5">
                {activeDay.slots.map((slot) => (
                  <button
                    key={`${slot.staff_id}-${slot.starts_at}`}
                    onClick={() =>
                      navigate(
                        `/book/${serviceId}/${staffId}/confirm?slot=${encodeURIComponent(slot.starts_at)}&slotStaffId=${slot.staff_id}`,
                      )
                    }
                    className="rounded-[var(--radius-control)] border border-charcoal-100 bg-white px-2 py-2.5 text-center text-sm font-medium text-charcoal-900 transition-colors hover:border-sage-400 active:bg-sage-50"
                  >
                    {new Intl.DateTimeFormat(undefined, {
                      hour: 'numeric',
                      minute: '2-digit',
                      timeZone: timezone,
                    }).format(new Date(slot.starts_at))}
                  </button>
                ))}
              </div>
            ) : (
              <p className="py-8 text-center text-sm text-charcoal-500">
                No open times in the next {WINDOW_DAYS} days
                {!isAnyStaff && staffMember ? ` for ${staffMember.display_name}` : ''}. Try another
                specialist.
              </p>
            )}
          </div>
        </>
      )}
    </div>
  )
}
