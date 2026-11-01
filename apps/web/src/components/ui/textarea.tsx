import * as React from 'react'
import { cn } from '@/lib/utils'

function Textarea({ className, ...props }: React.ComponentProps<'textarea'>) {
  return (
    <textarea
      data-slot="textarea"
      className={cn(
        'flex min-h-20 w-full rounded-[var(--radius-control)] border border-charcoal-300 bg-white px-3.5 py-2.5 text-sm text-charcoal-900 placeholder:text-charcoal-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage-400 disabled:opacity-50',
        className,
      )}
      {...props}
    />
  )
}

export { Textarea }
