import { ChevronRight, Clock, MapPin } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Card } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { DEMO_BUSINESS_SLUG } from '@/lib/config'
import { useBusinessProfile, useServices } from '@/lib/queries'
import { formatDuration, formatMoney } from '@/lib/utils'

export function HomePage() {
  const navigate = useNavigate()
  const { data: business, isLoading: businessLoading, isError: businessError } = useBusinessProfile(
    DEMO_BUSINESS_SLUG,
  )
  const { data: services, isLoading: servicesLoading } = useServices(business?.id)

  if (businessError) {
    return (
      <div className="p-6 text-center text-sm text-charcoal-500">
        Couldn't load this business. Please try again shortly.
      </div>
    )
  }

  const servicesByCategory = (services ?? []).reduce<Record<string, typeof services>>(
    (acc, service) => {
      const key = service.category ?? 'Services'
      acc[key] = [...(acc[key] ?? []), service]
      return acc
    },
    {},
  )

  return (
    <div>
      {/* Cover / hero */}
      <div className="relative h-24 w-full overflow-hidden bg-gradient-to-br from-sage-200 via-sage-100 to-ivory-soft">
        {business?.cover_image_url && (
          <img src={business.cover_image_url} alt="" className="h-full w-full object-cover" />
        )}
      </div>

      <div className="-mt-8 px-5">
        <Card className="p-5">
          {businessLoading ? (
            <div className="space-y-2">
              <Skeleton className="h-6 w-2/3" />
              <Skeleton className="h-4 w-full" />
            </div>
          ) : (
            <>
              <h1 className="font-display text-xl font-bold text-charcoal-900">{business?.name}</h1>
              {business?.description && (
                <p className="mt-1 text-sm text-charcoal-500">{business.description}</p>
              )}
              <div className="mt-3 flex flex-col gap-1.5 text-xs text-charcoal-500">
                {business?.address && (
                  <span className="flex items-center gap-1.5">
                    <MapPin className="size-3.5" /> {business.address}
                  </span>
                )}
                <span className="flex items-center gap-1.5">
                  <Clock className="size-3.5" /> Open today — see hours in staff schedule
                </span>
              </div>
            </>
          )}
        </Card>
      </div>

      <div className="mt-6 px-5">
        <h2 className="mb-3 text-sm font-semibold tracking-wide text-charcoal-500 uppercase">
          Choose a service
        </h2>

        {servicesLoading && (
          <div className="space-y-3">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-20 w-full" />
            ))}
          </div>
        )}

        <div className="space-y-6">
          {Object.entries(servicesByCategory).map(([category, items]) => (
            <div key={category}>
              <p className="mb-2 text-xs font-medium text-charcoal-300 uppercase">{category}</p>
              <div className="space-y-2.5">
                {items?.map((service) => (
                  <button
                    key={service.id}
                    onClick={() => navigate(`/book/${service.id}`)}
                    className="flex w-full items-center justify-between gap-3 rounded-[var(--radius-card)] border border-charcoal-100 bg-white p-4 text-left transition-colors hover:border-sage-300 active:bg-ivory-soft"
                  >
                    <div className="min-w-0">
                      <p className="truncate font-medium text-charcoal-900">{service.name}</p>
                      {service.description && (
                        <p className="mt-0.5 truncate text-xs text-charcoal-500">{service.description}</p>
                      )}
                      <p className="mt-1.5 text-xs text-charcoal-500">
                        {formatDuration(service.duration_minutes)} ·{' '}
                        {formatMoney(service.price_minor_units, service.currency)}
                      </p>
                    </div>
                    <ChevronRight className="size-5 shrink-0 text-charcoal-300" />
                  </button>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
