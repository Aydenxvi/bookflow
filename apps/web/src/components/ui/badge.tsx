import { cva, type VariantProps } from 'class-variance-authority'
import * as React from 'react'
import { cn } from '@/lib/utils'

const badgeVariants = cva(
  'inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium',
  {
    variants: {
      variant: {
        default: 'bg-charcoal-100 text-charcoal-700',
        accent: 'bg-sage-100 text-sage-700',
        pending: 'bg-status-pending/15 text-status-pending',
        confirmed: 'bg-status-confirmed/15 text-status-confirmed',
        completed: 'bg-status-completed/15 text-status-completed',
        cancelled: 'bg-status-cancelled/15 text-status-cancelled',
        noshow: 'bg-status-noshow/15 text-status-noshow',
      },
    },
    defaultVariants: { variant: 'default' },
  },
)

function Badge({
  className,
  variant,
  ...props
}: React.ComponentProps<'span'> & VariantProps<typeof badgeVariants>) {
  return <span data-slot="badge" className={cn(badgeVariants({ variant, className }))} {...props} />
}

export { Badge, badgeVariants }
