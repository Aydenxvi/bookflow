import { useState } from 'react'
import {
  Bar,
  CartesianGrid,
  Cell,
  ComposedChart,
  Line,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import type { BookingStatus } from '@/lib/admin-api-types'
import { useAdminAuth } from '@/lib/admin-auth'
import { useDashboardAnalytics } from '@/lib/admin-queries'
import { formatMoney } from '@/lib/utils'

// Same palette as components/StatusBadge.tsx / index.css's --color-status-*
// tokens, so a status means the same color everywhere in the admin UI.
const STATUS_COLOR: Record<BookingStatus, string> = {
  pending: '#b08a3e',
  confirmed: '#3f6b52',
  completed: '#596c46',
  cancelled: '#9a5a4c',
  no_show: '#7c7468',
}

const STATUS_LABEL: Record<BookingStatus, string> = {
  pending: 'Pending',
  confirmed: 'Confirmed',
  completed: 'Completed',
  cancelled: 'Cancelled',
  no_show: 'No-show',
}

export function AdminAnalyticsPage() {
  const { membership } = useAdminAuth()
  const [days, setDays] = useState(30)
  const { data, isLoading, isError } = useDashboardAnalytics(membership?.business_id, days)

  const dailyChartData = (data?.daily ?? []).map((d) => ({
    date: d.date,
    label: new Intl.DateTimeFormat(undefined, { month: 'short', day: 'numeric' }).format(new Date(d.date)),
    bookings: d.bookings_count,
    revenue: d.revenue_minor_units / 100,
  }))

  const totalRevenueMinorUnits = (data?.daily ?? []).reduce((sum, d) => sum + d.revenue_minor_units, 0)
  const totalBookings = (data?.daily ?? []).reduce((sum, d) => sum + d.bookings_count, 0)

  const statusChartData = (data?.status_breakdown ?? []).map((s) => ({
    status: s.status,
    label: STATUS_LABEL[s.status],
    count: s.count,
    color: STATUS_COLOR[s.status],
  }))

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-charcoal-900">Analytics</h1>
          <p className="mt-1 text-sm text-charcoal-500">
            Bookings and revenue trends for {membership?.business_name}.
          </p>
        </div>
        <Select
          className="w-40"
          value={String(days)}
          onChange={(e) => setDays(Number(e.target.value))}
          aria-label="Date range"
        >
          <option value="7">Last 7 days</option>
          <option value="30">Last 30 days</option>
          <option value="90">Last 90 days</option>
        </Select>
      </div>

      {isError && (
        <p className="mt-6 text-sm text-charcoal-500">Couldn't load analytics. Please try again shortly.</p>
      )}

      {isLoading ? (
        <div className="mt-6 space-y-4">
          <Skeleton className="h-80 w-full" />
          <Skeleton className="h-56 w-full" />
        </div>
      ) : data ? (
        <>
          <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
            <Card>
              <CardContent className="pt-5">
                <p className="text-2xl font-bold text-charcoal-900">{totalBookings}</p>
                <p className="text-xs text-charcoal-500">Bookings in range</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-5">
                <p className="text-2xl font-bold text-charcoal-900">
                  {formatMoney(totalRevenueMinorUnits, data.currency)}
                </p>
                <p className="text-xs text-charcoal-500">Completed revenue</p>
              </CardContent>
            </Card>
          </div>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="text-base">Bookings &amp; revenue over time</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-80 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={dailyChartData} margin={{ left: 0, right: 8, top: 8, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e0d8" vertical={false} />
                    <XAxis dataKey="label" tick={{ fontSize: 12, fill: '#6b6456' }} />
                    <YAxis
                      yAxisId="bookings"
                      allowDecimals={false}
                      tick={{ fontSize: 12, fill: '#6b6456' }}
                      width={32}
                    />
                    <YAxis
                      yAxisId="revenue"
                      orientation="right"
                      tick={{ fontSize: 12, fill: '#6b6456' }}
                      width={48}
                      tickFormatter={(v: number) => formatMoney(v * 100, data.currency)}
                    />
                    <Tooltip
                      formatter={(value, name) =>
                        name === 'revenue'
                          ? [formatMoney(Number(value ?? 0) * 100, data.currency), 'Revenue']
                          : [value, 'Bookings']
                      }
                    />
                    <Bar yAxisId="bookings" dataKey="bookings" fill="#b7c4a8" radius={[4, 4, 0, 0]} barSize={18} />
                    <Line
                      yAxisId="revenue"
                      type="monotone"
                      dataKey="revenue"
                      stroke="#3f6b52"
                      strokeWidth={2}
                      dot={false}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle className="text-base">Status breakdown</CardTitle>
            </CardHeader>
            <CardContent>
              {statusChartData.every((s) => s.count === 0) ? (
                <p className="text-sm text-charcoal-500">No bookings in this range.</p>
              ) : (
                <div className="flex flex-col items-center gap-6 sm:flex-row">
                  <div className="h-56 w-56 shrink-0">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={statusChartData}
                          dataKey="count"
                          nameKey="label"
                          innerRadius={55}
                          outerRadius={80}
                          paddingAngle={2}
                        >
                          {statusChartData.map((s) => (
                            <Cell key={s.status} fill={s.color} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                  <ul className="w-full space-y-2">
                    {statusChartData.map((s) => (
                      <li key={s.status} className="flex items-center justify-between text-sm">
                        <span className="flex items-center gap-2 text-charcoal-700">
                          <span className="size-2.5 rounded-full" style={{ backgroundColor: s.color }} />
                          {s.label}
                        </span>
                        <span className="font-medium text-charcoal-900">{s.count}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  )
}
