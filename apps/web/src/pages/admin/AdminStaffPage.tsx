import { CalendarOff, Pencil, Plus, Trash2 } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import {
  editableDaysToWeeklyScheduleUpdate,
  scheduleOutToEditableDays,
  ScheduleEditor,
  type EditableDay,
} from '@/components/admin/ScheduleEditor'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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
import type { AdminStaffOut, ScheduleExceptionType, StaffCreate, StaffUpdate } from '@/lib/admin-api-types'
import { useAdminAuth } from '@/lib/admin-auth'
import {
  useAdminServices,
  useAdminStaff,
  useCreateException,
  useCreateStaff,
  useDeleteException,
  useExceptions,
  useSetStaffSchedule,
  useSetStaffServices,
  useStaffSchedule,
  useUpdateStaff,
} from '@/lib/admin-queries'
import { ApiError } from '@/lib/api-client'

export function AdminStaffPage() {
  const { membership } = useAdminAuth()
  const businessId = membership!.business_id
  const { data: staff, isLoading, isError } = useAdminStaff(businessId)
  const { data: services } = useAdminServices(businessId)

  const [editing, setEditing] = useState<AdminStaffOut | 'new' | null>(null)
  const [scheduling, setScheduling] = useState<AdminStaffOut | null>(null)

  if (isError) {
    return <p className="text-sm text-charcoal-500">Couldn't load staff. Please try again shortly.</p>
  }

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-charcoal-900">Staff</h1>
          <p className="mt-1 text-sm text-charcoal-500">Who works at {membership?.business_name}.</p>
        </div>
        <Button onClick={() => setEditing('new')}>
          <Plus /> New staff member
        </Button>
      </div>

      {isLoading ? (
        <div className="mt-6 space-y-3">
          {[0, 1].map((i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </div>
      ) : (
        <div className="mt-6 space-y-2.5">
          {(staff ?? []).map((member) => (
            <Card key={member.id}>
              <CardContent className="flex items-center justify-between gap-3 pt-5">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-charcoal-900">{member.display_name}</p>
                    {!member.is_active && <Badge variant="cancelled">Inactive</Badge>}
                  </div>
                  {member.specialization && <p className="text-xs text-charcoal-500">{member.specialization}</p>}
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {member.service_ids.map((id) => {
                      const svc = services?.find((s) => s.id === id)
                      return svc ? (
                        <Badge key={id} variant="accent">
                          {svc.name}
                        </Badge>
                      ) : null
                    })}
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Button variant="outline" size="sm" onClick={() => setScheduling(member)}>
                    Schedule
                  </Button>
                  <Button variant="ghost" size="sm" onClick={() => setEditing(member)}>
                    <Pencil /> Edit
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
          {(staff ?? []).length === 0 && <p className="text-sm text-charcoal-500">No staff yet.</p>}
        </div>
      )}

      <div className="mt-8">
        <ExceptionsSection businessId={businessId} staff={staff ?? []} />
      </div>

      <StaffDialog
        businessId={businessId}
        target={editing}
        services={services ?? []}
        onClose={() => setEditing(null)}
      />
      {scheduling && (
        <ScheduleDialog businessId={businessId} staff={scheduling} onClose={() => setScheduling(null)} />
      )}
    </div>
  )
}

function StaffDialog({
  businessId,
  target,
  services,
  onClose,
}: {
  businessId: string
  target: AdminStaffOut | 'new' | null
  services: { id: string; name: string }[]
  onClose: () => void
}) {
  const isNew = target === 'new'
  const existing = isNew ? null : target
  const createStaff = useCreateStaff(businessId)
  const updateStaff = useUpdateStaff(businessId)
  const setStaffServices = useSetStaffServices(businessId)

  const [displayName, setDisplayName] = useState('')
  const [specialization, setSpecialization] = useState('')
  const [bio, setBio] = useState('')
  const [isActive, setIsActive] = useState(true)
  const [serviceIds, setServiceIds] = useState<string[]>([])

  const [openedFor, setOpenedFor] = useState<unknown>(null)
  if (target !== openedFor) {
    setOpenedFor(target)
    setDisplayName(existing?.display_name ?? '')
    setSpecialization(existing?.specialization ?? '')
    setBio(existing?.bio ?? '')
    setIsActive(existing?.is_active ?? true)
    setServiceIds(existing?.service_ids ?? [])
  }

  const pending = createStaff.isPending || updateStaff.isPending || setStaffServices.isPending
  const mutationError = createStaff.error ?? updateStaff.error ?? setStaffServices.error
  const errorMessage =
    mutationError instanceof ApiError ? mutationError.message : mutationError ? 'Something went wrong.' : null

  function toggleService(id: string) {
    setServiceIds((prev) => (prev.includes(id) ? prev.filter((s) => s !== id) : [...prev, id]))
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    try {
      if (isNew) {
        const body: StaffCreate = {
          display_name: displayName,
          specialization: specialization.trim() || null,
          bio: bio.trim() || null,
          service_ids: serviceIds,
        }
        await createStaff.mutateAsync(body)
      } else if (existing) {
        const body: StaffUpdate = {
          display_name: displayName,
          specialization: specialization.trim() || null,
          bio: bio.trim() || null,
          is_active: isActive,
        }
        await updateStaff.mutateAsync({ staffId: existing.id, body })
        await setStaffServices.mutateAsync({ staffId: existing.id, body: { service_ids: serviceIds } })
      }
      onClose()
    } catch {
      // surfaced via errorMessage above
    }
  }

  return (
    <Dialog open={target !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isNew ? 'New staff member' : `Edit ${existing?.display_name}`}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="staff-name">Display name</Label>
            <Input
              id="staff-name"
              value={displayName}
              onChange={(e) => setDisplayName(e.target.value)}
              required
              maxLength={160}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="staff-specialization">Specialization</Label>
            <Input
              id="staff-specialization"
              value={specialization}
              onChange={(e) => setSpecialization(e.target.value)}
              maxLength={160}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="staff-bio">Bio</Label>
            <Textarea id="staff-bio" value={bio} onChange={(e) => setBio(e.target.value)} maxLength={1000} />
          </div>

          {!isNew && (
            <label className="flex items-center gap-2 text-sm text-charcoal-700">
              <input type="checkbox" checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
              Active (unchecking hides them from the public booking flow)
            </label>
          )}

          <div className="space-y-1.5">
            <Label>Services offered</Label>
            {services.length === 0 ? (
              <p className="text-sm text-charcoal-500">No services yet — create one first.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {services.map((svc) => (
                  <button
                    type="button"
                    key={svc.id}
                    onClick={() => toggleService(svc.id)}
                    className={
                      serviceIds.includes(svc.id)
                        ? 'rounded-full bg-sage-600 px-3 py-1.5 text-xs font-medium text-ivory'
                        : 'rounded-full border border-charcoal-300 px-3 py-1.5 text-xs font-medium text-charcoal-700'
                    }
                  >
                    {svc.name}
                  </button>
                ))}
              </div>
            )}
          </div>

          {errorMessage && (
            <p className="rounded-[var(--radius-control)] bg-status-cancelled/10 p-3 text-sm text-status-cancelled">
              {errorMessage}
            </p>
          )}

          <DialogFooter>
            <Button type="submit" disabled={pending}>
              {pending ? 'Saving…' : isNew ? 'Create staff member' : 'Save changes'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function ScheduleDialog({
  businessId,
  staff,
  onClose,
}: {
  businessId: string
  staff: AdminStaffOut
  onClose: () => void
}) {
  const { data: schedule, isLoading } = useStaffSchedule(businessId, staff.id)
  const setSchedule = useSetStaffSchedule(businessId, staff.id)

  const [days, setDays] = useState<EditableDay[] | null>(null)

  if (schedule && days === null) {
    setDays(scheduleOutToEditableDays(schedule))
  }

  const errorMessage =
    setSchedule.error instanceof ApiError
      ? setSchedule.error.message
      : setSchedule.error
        ? 'Something went wrong.'
        : null

  async function handleSave() {
    try {
      await setSchedule.mutateAsync(editableDaysToWeeklyScheduleUpdate(days!))
      onClose()
    } catch {
      // surfaced via errorMessage above
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{staff.display_name}'s weekly schedule</DialogTitle>
        </DialogHeader>

        {isLoading || days === null ? (
          <Skeleton className="h-64 w-full" />
        ) : (
          <div className="max-h-[60vh] overflow-y-auto pr-1">
            <ScheduleEditor days={days} onChange={setDays} />
          </div>
        )}

        {errorMessage && (
          <p className="mt-3 rounded-[var(--radius-control)] bg-status-cancelled/10 p-3 text-sm text-status-cancelled">
            {errorMessage}
          </p>
        )}

        <DialogFooter>
          <Button onClick={handleSave} disabled={setSchedule.isPending || days === null}>
            {setSchedule.isPending ? 'Saving…' : 'Save schedule'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function ExceptionsSection({ businessId, staff }: { businessId: string; staff: AdminStaffOut[] }) {
  const { data: exceptions, isLoading } = useExceptions(businessId)
  const createException = useCreateException(businessId)
  const deleteException = useDeleteException(businessId)

  const [staffId, setStaffId] = useState('')
  const [date, setDate] = useState('')
  const [type, setType] = useState<ScheduleExceptionType>('leave')
  const [note, setNote] = useState('')

  const errorMessage =
    createException.error instanceof ApiError
      ? createException.error.message
      : createException.error
        ? 'Something went wrong.'
        : null

  async function handleAdd(e: FormEvent) {
    e.preventDefault()
    try {
      await createException.mutateAsync({
        staff_id: staffId || null,
        date,
        type,
        note: note.trim() || null,
      })
      setDate('')
      setNote('')
    } catch {
      // surfaced via errorMessage above
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-base">
          <CalendarOff className="size-4.5" /> Leave &amp; closures
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <form onSubmit={handleAdd} className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <div className="space-y-1.5">
            <Label htmlFor="exc-staff">Who</Label>
            <Select id="exc-staff" value={staffId} onChange={(e) => setStaffId(e.target.value)}>
              <option value="">Whole business</option>
              {staff.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.display_name}
                </option>
              ))}
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="exc-date">Date</Label>
            <Input id="exc-date" type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="exc-type">Type</Label>
            <Select id="exc-type" value={type} onChange={(e) => setType(e.target.value as ScheduleExceptionType)}>
              <option value="leave">Leave</option>
              <option value="holiday">Holiday</option>
              <option value="closure">Closure</option>
            </Select>
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="exc-note">Note</Label>
            <Input id="exc-note" value={note} onChange={(e) => setNote(e.target.value)} maxLength={300} />
          </div>
          <div className="col-span-full">
            <Button type="submit" size="sm" disabled={createException.isPending || !date}>
              {createException.isPending ? 'Adding…' : 'Add'}
            </Button>
          </div>
        </form>

        {errorMessage && (
          <p className="rounded-[var(--radius-control)] bg-status-cancelled/10 p-3 text-sm text-status-cancelled">
            {errorMessage}
          </p>
        )}

        {isLoading ? (
          <Skeleton className="h-16 w-full" />
        ) : (exceptions ?? []).length === 0 ? (
          <p className="text-sm text-charcoal-500">No leave or closures scheduled.</p>
        ) : (
          <ul className="space-y-2">
            {exceptions!.map((exc) => {
              const who = exc.staff_id ? staff.find((s) => s.id === exc.staff_id)?.display_name ?? 'Staff' : 'Whole business'
              return (
                <li key={exc.id} className="flex items-center justify-between gap-3 text-sm">
                  <span className="text-charcoal-700">
                    <span className="font-medium text-charcoal-900">{exc.date}</span> — {who} · {exc.type}
                    {exc.note ? ` · ${exc.note}` : ''}
                  </span>
                  <button
                    onClick={() => deleteException.mutate(exc.id)}
                    className="text-charcoal-500 hover:text-status-cancelled"
                  >
                    <Trash2 className="size-4" />
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
