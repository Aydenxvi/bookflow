import { ChevronDown } from 'lucide-react'
import * as React from 'react'
import { cn } from '@/lib/utils'

/**
 * A plain native <select>, styled to match the rest of the design system.
 * No Radix Select is installed in this project (just the primitives already
 * in package.json) — a native select is simpler, fully accessible, and
 * plenty for the admin dashboard's handful of pickers (staff, service,
 * status, weekday).
 */
function Select({ className, children, ...props }: React.ComponentProps<'select'>) {
  return (
    <div className="relative">
      <select
        data-slot="select"
        className={cn(
          'h-11 w-full appearance-none rounded-[var(--radius-control)] border border-charcoal-300 bg-white px-3.5 pr-9 text-sm text-charcoal-900 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage-400 disabled:opacity-50',
          className,
        )}
        {...props}
      >
        {children}
      </select>
      <ChevronDown className="pointer-events-none absolute top-1/2 right-3 size-4 -translate-y-1/2 text-charcoal-500" />
    </div>
  )
}

export { Select }
