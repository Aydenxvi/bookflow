import { useState, type FormEvent } from 'react'
import {
  editableDaysToWeeklyScheduleUpdate,
  scheduleOutToEditableDays,
  ScheduleEditor,
  type EditableDay,
} from '@/components/admin/ScheduleEditor'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import type { BookingConfirmationMode, BookingPolicyUpdate, BusinessProfileUpdate } from '@/lib/admin-api-types'
import { useAdminAuth } from '@/lib/admin-auth'
import {
  useAdminProfile,
  useBookingPolicy,
  useBusinessHours,
  useSetBusinessHours,
  useUpdateBookingPolicy,
  useUpdateProfile,
} from '@/lib/admin-queries'
import { ApiError } from '@/lib/api-client'

export function AdminSettingsPage() {
  const { membership } = useAdminAuth()
  const businessId = membership!.business_id

  return (
    <div className="space-y-6">
      <div>
        <h1 className="font-display text-2xl font-bold text-charcoal-900">Settings</h1>
        <p className="mt-1 text-sm text-charcoal-500">Profile, operating hours, and booking policy.</p>
      </div>

      <ProfileCard businessId={businessId} />
      <HoursCard businessId={businessId} />
      <PolicyCard businessId={businessId} />
    </div>
  )
}

function ProfileCard({ businessId }: { businessId: string }) {
  const { data: profile, isLoading } = useAdminProfile(businessId)
  const updateProfile = useUpdateProfile(businessId)

  const [form, setForm] = useState<BusinessProfileUpdate | null>(null)
  if (profile && form === null) {
    setForm({
      name: profile.name,
      description: profile.description ?? '',
      address: profile.address ?? '',
      contact_phone: profile.contact_phone ?? '',
      contact_email: profile.contact_email ?? '',
      timezone: profile.timezone,
      currency: profile.currency,
    })
  }

  const errorMessage =
    updateProfile.error instanceof ApiError
      ? updateProfile.error.message
      : updateProfile.error
        ? 'Something went wrong.'
        : null

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    try {
      await updateProfile.mutateAsync(form!)
    } catch {
      // surfaced via errorMessage above
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Business profile</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading || form === null ? (
          <Skeleton className="h-48 w-full" />
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="space-y-1.5">
                <Label htmlFor="biz-name">Name</Label>
                <Input
                  id="biz-name"
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  required
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="biz-address">Address</Label>
                <Input
                  id="biz-address"
                  value={form.address ?? ''}
                  onChange={(e) => setForm({ ...form, address: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="biz-phone">Contact phone</Label>
                <Input
                  id="biz-phone"
                  value={form.contact_phone ?? ''}
                  onChange={(e) => setForm({ ...form, contact_phone: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="biz-email">Contact email</Label>
                <Input
                  id="biz-email"
                  type="email"
                  value={form.contact_email ?? ''}
                  onChange={(e) => setForm({ ...form, contact_email: e.target.value })}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="biz-timezone">Timezone (IANA)</Label>
                <Input
                  id="biz-timezone"
                  value={form.timezone}
                  onChange={(e) => setForm({ ...form, timezone: e.target.value })}
                  placeholder="Europe/Istanbul"
                  required
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="biz-currency">Currency</Label>
                <Input
                  id="biz-currency"
                  value={form.currency}
                  onChange={(e) => setForm({ ...form, currency: e.target.value.toUpperCase() })}
                  maxLength={8}
                  required
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <Label htmlFor="biz-description">Description</Label>
              <Textarea
                id="biz-description"
                value={form.description ?? ''}
                onChange={(e) => setForm({ ...form, description: e.target.value })}
                maxLength={2000}
              />
            </div>

            {errorMessage && (
              <p className="rounded-[var(--radius-control)] bg-status-cancelled/10 p-3 text-sm text-status-cancelled">
                {errorMessage}
              </p>
            )}

            <Button type="submit" disabled={updateProfile.isPending}>
              {updateProfile.isPending ? 'Saving…' : 'Save profile'}
            </Button>
          </form>
        )}
      </CardContent>
    </Card>
  )
}

function HoursCard({ businessId }: { businessId: string }) {
  const { data: hours, isLoading } = useBusinessHours(businessId)
  const setHours = useSetBusinessHours(businessId)

  const [days, setDays] = useState<EditableDay[] | null>(null)
  if (hours && days === null) {
    setDays(scheduleOutToEditableDays(hours))
  }

  const errorMessage =
    setHours.error instanceof ApiError ? setHours.error.message : setHours.error ? 'Something went wrong.' : null

  async function handleSave() {
    try {
      await setHours.mutateAsync(editableDaysToWeeklyScheduleUpdate(days!))
    } catch {
      // surfaced via errorMessage above
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Operating hours</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {isLoading || days === null ? (
          <Skeleton className="h-64 w-full" />
        ) : (
          <ScheduleEditor days={days} onChange={setDays} />
        )}

        {errorMessage && (
          <p className="rounded-[var(--radius-control)] bg-status-cancelled/10 p-3 text-sm text-status-cancelled">
            {errorMessage}
          </p>
        )}

        <Button onClick={handleSave} disabled={setHours.isPending || days === null}>
          {setHours.isPending ? 'Saving…' : 'Save hours'}
        </Button>
      </CardContent>
    </Card>
  )
}

function PolicyCard({ businessId }: { businessId: string }) {
  const { data: policy, isLoading } = useBookingPolicy(businessId)
  const updatePolicy = useUpdateBookingPolicy(businessId)

  const [form, setForm] = useState<BookingPolicyUpdate | null>(null)
  if (policy && form === null) {
    setForm({ ...policy })
  }

  const errorMessage =
    updatePolicy.error instanceof ApiError
      ? updatePolicy.error.message
      : updatePolicy.error
        ? 'Something went wrong.'
        : null

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    try {
      await updatePolicy.mutateAsync(form!)
    } catch {
      // surfaced via errorMessage above
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Booking policy</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading || form === null ? (
          <Skeleton className="h-48 w-full" />
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div className="space-y-1.5">
                <Label htmlFor="pol-confirmation">Confirmation mode</Label>
                <Select
                  id="pol-confirmation"
                  value={form.confirmation_mode}
                  onChange={(e) =>
                    setForm({ ...form, confirmation_mode: e.target.value as BookingConfirmationMode })
                  }
                >
                  <option value="automatic">Automatic</option>
                  <option value="manual">Manual review</option>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="pol-slot">Slot interval (min)</Label>
                <Input
                  id="pol-slot"
                  type="number"
                  min={1}
                  max={120}
                  value={form.slot_interval_minutes}
                  onChange={(e) => setForm({ ...form, slot_interval_minutes: Number(e.target.value) })}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="pol-buffer">Buffer between bookings (min)</Label>
                <Input
                  id="pol-buffer"
                  type="number"
                  min={0}
                  max={240}
                  value={form.buffer_minutes}
                  onChange={(e) => setForm({ ...form, buffer_minutes: Number(e.target.value) })}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="pol-lead">Minimum lead time (min)</Label>
                <Input
                  id="pol-lead"
                  type="number"
                  min={0}
                  value={form.min_lead_time_minutes}
                  onChange={(e) => setForm({ ...form, min_lead_time_minutes: Number(e.target.value) })}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="pol-advance">Max advance booking (days)</Label>
                <Input
                  id="pol-advance"
                  type="number"
                  min={1}
                  max={365}
                  value={form.max_advance_days}
                  onChange={(e) => setForm({ ...form, max_advance_days: Number(e.target.value) })}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="pol-cancel">Cancellation window (min)</Label>
                <Input
                  id="pol-cancel"
                  type="number"
                  min={0}
                  value={form.cancellation_window_minutes}
                  onChange={(e) => setForm({ ...form, cancellation_window_minutes: Number(e.target.value) })}
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="pol-reschedule">Reschedule window (min)</Label>
                <Input
                  id="pol-reschedule"
                  type="number"
                  min={0}
                  value={form.reschedule_window_minutes}
                  onChange={(e) => setForm({ ...form, reschedule_window_minutes: Number(e.target.value) })}
                />
              </div>
            </div>

            {errorMessage && (
              <p className="rounded-[var(--radius-control)] bg-status-cancelled/10 p-3 text-sm text-status-cancelled">
                {errorMessage}
              </p>
            )}

            <Button type="submit" disabled={updatePolicy.isPending}>
              {updatePolicy.isPending ? 'Saving…' : 'Save policy'}
            </Button>
          </form>
        )}
      </CardContent>
    </Card>
  )
}
