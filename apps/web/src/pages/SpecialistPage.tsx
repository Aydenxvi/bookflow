import { ChevronLeft, ChevronRight, Sparkles, User } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'
import { Skeleton } from '@/components/ui/skeleton'
import { DEMO_BUSINESS_SLUG } from '@/lib/config'
import { useBusinessProfile, useServices, useStaff } from '@/lib/queries'
import { ANY_STAFF_SENTINEL } from '@/lib/api-types'

export function SpecialistPage() {
  const { serviceId } = useParams<{ serviceId: string }>()
  const navigate = useNavigate()
  const { data: business } = useBusinessProfile(DEMO_BUSINESS_SLUG)
  const { data: services } = useServices(business?.id)
  const { data: staff, isLoading } = useStaff(business?.id, serviceId)

  const service = services?.find((s) => s.id === serviceId)

  return (
    <div className="p-5">
      <button
        onClick={() => navigate('/')}
        className="mb-4 flex items-center gap-1 text-sm text-charcoal-500 hover:text-charcoal-900"
      >
        <ChevronLeft className="size-4" /> Back
      </button>

      <h1 className="font-display text-xl font-bold text-charcoal-900">Choose a specialist</h1>
      {service && <p className="mt-1 text-sm text-charcoal-500">{service.name}</p>}

      <div className="mt-5 space-y-2.5">
        <button
          onClick={() => navigate(`/book/${serviceId}/${ANY_STAFF_SENTINEL}`)}
          className="flex w-full items-center gap-3 rounded-[var(--radius-card)] border border-sage-300 bg-sage-50 p-4 text-left transition-colors hover:border-sage-400 active:bg-sage-100"
        >
          <div className="flex size-11 shrink-0 items-center justify-center rounded-full bg-sage-200 text-sage-700">
            <Sparkles className="size-5" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="font-medium text-charcoal-900">Any available specialist</p>
            <p className="text-xs text-charcoal-500">Soonest appointment, matched automatically</p>
          </div>
          <ChevronRight className="size-5 shrink-0 text-charcoal-300" />
        </button>

        {isLoading &&
          [0, 1].map((i) => <Skeleton key={i} className="h-[72px] w-full" />)}

        {staff?.map((s) => (
          <button
            key={s.id}
            onClick={() => navigate(`/book/${serviceId}/${s.id}`)}
            className="flex w-full items-center gap-3 rounded-[var(--radius-card)] border border-charcoal-100 bg-white p-4 text-left transition-colors hover:border-sage-300 active:bg-ivory-soft"
          >
            <div className="flex size-11 shrink-0 items-center justify-center overflow-hidden rounded-full bg-charcoal-100 text-charcoal-500">
              {s.photo_url ? (
                <img src={s.photo_url} alt={s.display_name} className="h-full w-full object-cover" />
              ) : (
                <User className="size-5" />
              )}
            </div>
            <div className="min-w-0 flex-1">
              <p className="font-medium text-charcoal-900">{s.display_name}</p>
              {s.specialization && <p className="text-xs text-charcoal-500">{s.specialization}</p>}
            </div>
            <ChevronRight className="size-5 shrink-0 text-charcoal-300" />
          </button>
        ))}

        {!isLoading && staff?.length === 0 && (
          <p className="py-6 text-center text-sm text-charcoal-500">
            No specialists currently offer this service.
          </p>
        )}
      </div>
    </div>
  )
}
