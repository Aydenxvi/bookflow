import { Slot } from '@radix-ui/react-slot'
import { cva, type VariantProps } from 'class-variance-authority'
import * as React from 'react'
import { cn } from '@/lib/utils'

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-[var(--radius-control)] text-sm font-medium transition-colors disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sage-400 focus-visible:ring-offset-2",
  {
    variants: {
      variant: {
        default: 'bg-charcoal-900 text-ivory hover:bg-charcoal-800 active:bg-charcoal-900',
        accent: 'bg-sage-600 text-ivory hover:bg-sage-700 active:bg-sage-700',
        outline:
          'border border-charcoal-300 bg-transparent text-charcoal-900 hover:bg-charcoal-50',
        ghost: 'bg-transparent text-charcoal-900 hover:bg-charcoal-50',
        subtle: 'bg-ivory-soft text-charcoal-900 hover:bg-beige',
        destructive: 'bg-transparent text-status-cancelled hover:bg-status-cancelled/10',
        link: 'text-sage-700 underline-offset-4 hover:underline',
      },
      size: {
        default: 'h-11 px-5',
        sm: 'h-9 px-3.5 text-[0.8125rem]',
        lg: 'h-13 px-6 text-base',
        icon: 'size-10',
      },
    },
    defaultVariants: {
      variant: 'default',
      size: 'default',
    },
  },
)

function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: React.ComponentProps<'button'> &
  VariantProps<typeof buttonVariants> & { asChild?: boolean }) {
  const Comp = asChild ? Slot : 'button'
  return (
    <Comp data-slot="button" className={cn(buttonVariants({ variant, size, className }))} {...props} />
  )
}

export { Button, buttonVariants }
