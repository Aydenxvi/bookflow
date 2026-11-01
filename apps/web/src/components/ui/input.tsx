import * as React from 'react'
import { cn } from '@/lib/utils'

function Input({ className, type, ...props }: React.ComponentProps<'input'>) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        'flex h-11 w-full rounded-[var(--radius-control)] border border-charcoal-300 bg-white px-3.5 text-sm text-charcoal-900 placeholder:text-charcoal-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage-400 disabled:opacity-50',
        className,
      )}
      {...props}
    />
  )
}

export { Input }
