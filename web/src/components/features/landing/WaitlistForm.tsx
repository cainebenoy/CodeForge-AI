'use client'

import { useState, FormEvent } from 'react'
import { Mail, ArrowRight, Check, Loader2, AlertCircle } from 'lucide-react'
import { toast } from '@/lib/hooks/use-toast'

interface WaitlistFormProps {
  /** Title displayed above the form */
  title?: string
  /** Description text */
  description?: string
  /** Placeholder text for email input */
  placeholder?: string
  /** Button text */
  buttonText?: string
  /** Layout orientation */
  layout?: 'horizontal' | 'vertical'
  /** Additional className */
  className?: string
}

/**
 * WaitlistForm — Email capture form for waitlist signups.
 * 
 * Features:
 * - Email validation
 * - Loading state
 * - Success/error feedback via toast
 * - Stores locally (until backend endpoint is configured)
 */
export function WaitlistForm({
  title = 'Join the Waitlist',
  description = 'Be the first to know when we launch new features.',
  placeholder = 'Enter your email',
  buttonText = 'Join Waitlist',
  layout = 'horizontal',
  className = '',
}: WaitlistFormProps) {
  const [email, setEmail] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const validateEmail = (email: string): boolean => {
    const regex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    return regex.test(email)
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null)

    if (!email.trim()) {
      setError('Please enter your email address')
      return
    }

    if (!validateEmail(email)) {
      setError('Please enter a valid email address')
      return
    }

    setIsSubmitting(true)

    try {
      // Use backend endpoint
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/v1/waitlist/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      })

      if (!response.ok) {
        throw new Error('Failed to join waitlist')
      }

      setIsSubmitted(true)
      setEmail('')

      toast.success("You're on the list!", "We'll notify you when new features are available.")
    } catch (err) {
      console.error(err)
      setError('Something went wrong. Please try again.')
      toast.error('Submission failed', 'Please try again later.')
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isSubmitted) {
    return (
      <div className={`flex flex-col items-center gap-3 ${className}`}>
        <div className="size-12 rounded-full bg-emerald-500/10 flex items-center justify-center">
          <Check className="size-6 text-emerald-500" />
        </div>
        <p className="text-lg font-medium text-foreground">You&apos;re on the list!</p>
        <p className="text-sm text-muted-foreground">We&apos;ll be in touch soon.</p>
      </div>
    )
  }

  const isVertical = layout === 'vertical'

  return (
    <div className={`${className}`}>
      {/* Header */}
      {(title || description) && (
        <div className={`${isVertical ? 'text-center mb-4' : 'mb-4'}`}>
          {title && (
            <h3 className="text-lg font-semibold text-foreground mb-1">{title}</h3>
          )}
          {description && (
            <p className="text-sm text-muted-foreground">{description}</p>
          )}
        </div>
      )}

      {/* Form */}
      <form
        onSubmit={handleSubmit}
        className={`flex ${isVertical ? 'flex-col' : 'flex-col sm:flex-row'} gap-3`}
      >
        <div className="relative flex-1">
          <Mail className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
          <input
            type="email"
            value={email}
            onChange={(e) => {
              setEmail(e.target.value)
              setError(null)
            }}
            placeholder={placeholder}
            className={`w-full h-11 pl-10 pr-4 bg-muted border rounded-lg text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-cf-primary/50 transition-colors ${
              error ? 'border-destructive' : 'border-border focus:border-cf-primary'
            }`}
            disabled={isSubmitting}
          />
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className={`h-11 px-6 bg-cf-primary hover:bg-cf-primary/90 text-white rounded-lg text-sm font-semibold flex items-center justify-center gap-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
            isVertical ? 'w-full' : 'w-full sm:w-auto'
          }`}
        >
          {isSubmitting ? (
            <>
              <Loader2 className="size-4 animate-spin" />
              Submitting...
            </>
          ) : (
            <>
              {buttonText}
              <ArrowRight className="size-4" />
            </>
          )}
        </button>
      </form>

      {/* Error message */}
      {error && (
        <div className="flex items-center gap-2 mt-2 text-sm text-destructive">
          <AlertCircle className="size-4" />
          <span>{error}</span>
        </div>
      )}

      {/* Privacy note */}
      <p className="text-xs text-muted-foreground mt-3 text-center">
        No spam, ever. Unsubscribe anytime.
      </p>
    </div>
  )
}

/**
 * WaitlistBanner — Full-width banner version of the waitlist form.
 * Designed to be placed before the footer.
 */
export function WaitlistBanner({ className = '' }: { className?: string }) {
  return (
    <section className={`py-16 px-4 sm:px-6 lg:px-8 bg-muted/30 border-t border-border ${className}`}>
      <div className="max-w-xl mx-auto">
        <WaitlistForm
          title="Stay in the Loop"
          description="Get notified about new AI agents, features, and updates. No spam, just the good stuff."
          buttonText="Subscribe"
          layout="horizontal"
        />
      </div>
    </section>
  )
}
