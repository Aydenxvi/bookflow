import { BookingCard } from '@/components/BookingCard'
import { Skeleton } from '@/components/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useMyBookings } from '@/lib/queries'

export function AppointmentsPage() {
  const { data, isLoading, isError } = useMyBookings()

  return (
    <div className="p-5">
      <h1 className="font-display text-xl font-bold text-charcoal-900">My Appointments</h1>

      {isLoading && (
        <div className="mt-5 space-y-3">
          {[0, 1].map((i) => (
            <Skeleton key={i} className="h-32 w-full" />
          ))}
        </div>
      )}

      {isError && (
        <p className="mt-6 text-center text-sm text-charcoal-500">
          Couldn't load your appointments. Please try again shortly.
        </p>
      )}

      {data && (
        <Tabs defaultValue="upcoming" className="mt-5">
          <TabsList className="w-full">
            <TabsTrigger value="upcoming">Upcoming</TabsTrigger>
            <TabsTrigger value="completed">Completed</TabsTrigger>
            <TabsTrigger value="cancelled">Cancelled</TabsTrigger>
          </TabsList>

          <TabsContent value="upcoming" className="space-y-3">
            {data.upcoming.length === 0 ? (
              <EmptyState message="No upcoming appointments yet." />
            ) : (
              data.upcoming.map((b) => <BookingCard key={b.id} booking={b} canAct />)
            )}
          </TabsContent>

          <TabsContent value="completed" className="space-y-3">
            {data.completed.length === 0 ? (
              <EmptyState message="No completed appointments yet." />
            ) : (
              data.completed.map((b) => <BookingCard key={b.id} booking={b} canAct={false} />)
            )}
          </TabsContent>

          <TabsContent value="cancelled" className="space-y-3">
            {data.cancelled.length === 0 ? (
              <EmptyState message="No cancelled appointments." />
            ) : (
              data.cancelled.map((b) => <BookingCard key={b.id} booking={b} canAct={false} />)
            )}
          </TabsContent>
        </Tabs>
      )}
    </div>
  )
}

function EmptyState({ message }: { message: string }) {
  return <p className="py-10 text-center text-sm text-charcoal-500">{message}</p>
}
