import { CalendarClock, CheckCircle2, Clock, XCircle } from 'lucide-react'
import type { ComponentType } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useAdminAuth } from '@/lib/admin-auth'
import { useAdminDashboard } from '@/lib/admin-queries'
import { formatMoney } from '@/lib/utils'

export function AdminDashboardPage() {
  const { membership } = useAdminAuth()
  const { data, isLoading, isError } = useAdminDashboard(membership?.business_id)

  if (isError) {
    return <p className="text-sm text-charcoal-500">Couldn't load the dashboard. Please try again shortly.</p>
  }

  return (
    <div>
      <h1 className="font-display text-2xl font-bold text-charcoal-900">Dashboard</h1>
      <p className="mt-1 text-sm text-charcoal-500">An overview of {membership?.business_name}'s activity.</p>

      {isLoading ? (
        <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
          {[0, 1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-28 w-full" />
          ))}
        </div>
      ) : data ? (
        <>
          <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
            <StatCard icon={CalendarClock} label="Today" value={data.today_count} accent="sage" />
            <StatCard icon={Clock} label="Upcoming" value={data.upcoming_count} accent="default" />
            <StatCard icon={CheckCircle2} label="Completed" value={data.completed_count} accent="default" />
            <StatCard icon={XCircle} label="Cancelled" value={data.cancelled_count} accent="default" />
          </div>

          <div className="mt-6 grid grid-cols-1 gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle className="text-base">Revenue (completed)</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-display text-3xl font-bold text-charcoal-900">
                  {formatMoney(data.revenue_minor_units, data.revenue_currency)}
                </p>
                <p className="mt-1 text-xs text-charcoal-500">
                  Estimated from completed bookings' price at the time they were made.
                </p>
              </CardContent>
            </Card>

            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle className="text-base">Popular services</CardTitle>
              </CardHeader>
              <CardContent>
                {data.popular_services.length === 0 ? (
                  <p className="text-sm text-charcoal-500">No bookings yet.</p>
                ) : (
                  <ul className="space-y-2">
                    {data.popular_services.map((s) => (
                      <li key={s.service_id} className="flex items-center justify-between text-sm">
                        <span className="text-charcoal-700">{s.name}</span>
                        <span className="font-medium text-charcoal-900">{s.count}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>

            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle className="text-base">Staff workload</CardTitle>
              </CardHeader>
              <CardContent>
                {data.staff_workload.length === 0 ? (
                  <p className="text-sm text-charcoal-500">No active bookings right now.</p>
                ) : (
                  <ul className="space-y-2">
                    {data.staff_workload.map((s) => (
                      <li key={s.staff_id} className="flex items-center justify-between text-sm">
                        <span className="text-charcoal-700">{s.display_name}</span>
                        <span className="font-medium text-charcoal-900">{s.count}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </div>
        </>
      ) : null}
    </div>
  )
}

function StatCard({
  icon: Icon,
  label,
  value,
  accent,
}: {
  icon: ComponentType<{ className?: string }>
  label: string
  value: number
  accent: 'sage' | 'default'
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-3 pt-5">
        <div
          className={
            accent === 'sage'
              ? 'flex size-10 items-center justify-center rounded-full bg-sage-100 text-sage-700'
              : 'flex size-10 items-center justify-center rounded-full bg-charcoal-100 text-charcoal-700'
          }
        >
          <Icon className="size-5" />
        </div>
        <div>
          <p className="text-2xl font-bold text-charcoal-900">{value}</p>
          <p className="text-xs text-charcoal-500">{label}</p>
        </div>
      </CardContent>
    </Card>
  )
}
