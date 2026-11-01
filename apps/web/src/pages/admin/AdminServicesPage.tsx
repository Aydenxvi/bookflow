import { Archive, ArchiveRestore, Pencil, Plus } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { useAdminAuth } from '@/lib/admin-auth'
import type { AdminServiceOut, ServiceCreate, ServiceUpdate } from '@/lib/admin-api-types'
import { useAdminServices, useCreateService, useSetServiceArchived, useUpdateService } from '@/lib/admin-queries'
import { ApiError } from '@/lib/api-client'
import { formatDuration, formatMoney } from '@/lib/utils'

export function AdminServicesPage() {
  const { membership } = useAdminAuth()
  const businessId = membership!.business_id
  const { data: services, isLoading, isError } = useAdminServices(businessId)
  const setArchived = useSetServiceArchived(businessId)

  const [editing, setEditing] = useState<AdminServiceOut | 'new' | null>(null)

  if (isError) {
    return <p className="text-sm text-charcoal-500">Couldn't load services. Please try again shortly.</p>
  }

  const active = (services ?? []).filter((s) => s.is_active)
  const archived = (services ?? []).filter((s) => !s.is_active)

  return (
    <div>
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-bold text-charcoal-900">Services</h1>
          <p className="mt-1 text-sm text-charcoal-500">What {membership?.business_name} offers customers.</p>
        </div>
        <Button onClick={() => setEditing('new')}>
          <Plus /> New service
        </Button>
      </div>

      {isLoading ? (
        <div className="mt-6 space-y-3">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-20 w-full" />
          ))}
        </div>
      ) : (
        <div className="mt-6 space-y-6">
          <ServiceGroup
            title="Active"
            services={active}
            onEdit={setEditing}
            onToggleArchive={(s) => setArchived.mutate({ serviceId: s.id, archived: true })}
            toggleLabel="Archive"
            toggleIcon={Archive}
          />
          {archived.length > 0 && (
            <ServiceGroup
              title="Archived"
              services={archived}
              onEdit={setEditing}
              onToggleArchive={(s) => setArchived.mutate({ serviceId: s.id, archived: false })}
              toggleLabel="Restore"
              toggleIcon={ArchiveRestore}
            />
          )}
        </div>
      )}

      <ServiceDialog businessId={businessId} target={editing} onClose={() => setEditing(null)} />
    </div>
  )
}

function ServiceGroup({
  title,
  services,
  onEdit,
  onToggleArchive,
  toggleLabel,
  toggleIcon: ToggleIcon,
}: {
  title: string
  services: AdminServiceOut[]
  onEdit: (s: AdminServiceOut) => void
  onToggleArchive: (s: AdminServiceOut) => void
  toggleLabel: string
  toggleIcon: typeof Archive
}) {
  if (services.length === 0) {
    return (
      <div>
        <h2 className="mb-2 text-xs font-semibold tracking-wide text-charcoal-500 uppercase">{title}</h2>
        <p className="text-sm text-charcoal-500">None yet.</p>
      </div>
    )
  }

  return (
    <div>
      <h2 className="mb-2 text-xs font-semibold tracking-wide text-charcoal-500 uppercase">{title}</h2>
      <div className="space-y-2.5">
        {services.map((service) => (
          <Card key={service.id}>
            <CardContent className="flex items-center justify-between gap-3 pt-5">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <p className="font-medium text-charcoal-900">{service.name}</p>
                  {service.category && <Badge>{service.category}</Badge>}
                </div>
                <p className="mt-1 text-xs text-charcoal-500">
                  {formatDuration(service.duration_minutes)} ·{' '}
                  {formatMoney(service.price_minor_units, service.currency)}
                </p>
              </div>
              <div className="flex shrink-0 items-center gap-2">
                <Button variant="outline" size="sm" onClick={() => onEdit(service)}>
                  <Pencil /> Edit
                </Button>
                <Button variant="ghost" size="sm" onClick={() => onToggleArchive(service)}>
                  <ToggleIcon /> {toggleLabel}
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}

function ServiceDialog({
  businessId,
  target,
  onClose,
}: {
  businessId: string
  target: AdminServiceOut | 'new' | null
  onClose: () => void
}) {
  const isNew = target === 'new'
  const existing = isNew ? null : target
  const createService = useCreateService(businessId)
  const updateService = useUpdateService(businessId)

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [category, setCategory] = useState('')
  const [duration, setDuration] = useState('30')
  const [price, setPrice] = useState('0')
  const [currency, setCurrency] = useState('USD')

  // Reset the form fields whenever a different target opens.
  const [openedFor, setOpenedFor] = useState<unknown>(null)
  if (target !== openedFor) {
    setOpenedFor(target)
    setName(existing?.name ?? '')
    setDescription(existing?.description ?? '')
    setCategory(existing?.category ?? '')
    setDuration(String(existing?.duration_minutes ?? 30))
    setPrice(existing ? (existing.price_minor_units / 100).toFixed(2) : '0.00')
    setCurrency(existing?.currency ?? 'USD')
  }

  const mutation = isNew ? createService : updateService
  const errorMessage =
    mutation.error instanceof ApiError ? mutation.error.message : mutation.error ? 'Something went wrong.' : null

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const priceMinorUnits = Math.round(parseFloat(price || '0') * 100)
    try {
      if (isNew) {
        const body: ServiceCreate = {
          name,
          description: description.trim() || null,
          category: category.trim() || null,
          duration_minutes: parseInt(duration, 10),
          price_minor_units: priceMinorUnits,
          currency,
        }
        await createService.mutateAsync(body)
      } else if (existing) {
        const body: ServiceUpdate = {
          name,
          description: description.trim() || null,
          category: category.trim() || null,
          duration_minutes: parseInt(duration, 10),
          price_minor_units: priceMinorUnits,
          currency,
        }
        await updateService.mutateAsync({ serviceId: existing.id, body })
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
          <DialogTitle>{isNew ? 'New service' : `Edit ${existing?.name}`}</DialogTitle>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="svc-name">Name</Label>
            <Input id="svc-name" value={name} onChange={(e) => setName(e.target.value)} required maxLength={160} />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="svc-description">Description</Label>
            <Textarea
              id="svc-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={1000}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="svc-category">Category</Label>
            <Input id="svc-category" value={category} onChange={(e) => setCategory(e.target.value)} maxLength={80} />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div className="space-y-1.5">
              <Label htmlFor="svc-duration">Duration (min)</Label>
              <Input
                id="svc-duration"
                type="number"
                min={1}
                max={600}
                value={duration}
                onChange={(e) => setDuration(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="svc-price">Price</Label>
              <Input
                id="svc-price"
                type="number"
                min={0}
                step="0.01"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="svc-currency">Currency</Label>
              <Input
                id="svc-currency"
                value={currency}
                onChange={(e) => setCurrency(e.target.value.toUpperCase())}
                maxLength={8}
                required
              />
            </div>
          </div>

          {errorMessage && (
            <p className="rounded-[var(--radius-control)] bg-status-cancelled/10 p-3 text-sm text-status-cancelled">
              {errorMessage}
            </p>
          )}

          <DialogFooter>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending ? 'Saving…' : isNew ? 'Create service' : 'Save changes'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}
