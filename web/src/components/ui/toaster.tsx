'use client'

import { useToastState, type ToastVariant } from '@/lib/hooks/use-toast'
import { X } from 'lucide-react'

const variantClasses: Record<ToastVariant, string> = {
  default:
    'bg-background border-border text-foreground',
  success:
    'bg-emerald-950/90 border-emerald-600/30 text-emerald-100',
  error:
    'bg-red-950/90 border-red-600/30 text-red-100',
  warning:
    'bg-amber-950/90 border-amber-600/30 text-amber-100',
}

/**
 * Global toast renderer — mount once in the root layout.
 * Displays toasts stacked in the bottom-right corner.
 */
export function Toaster() {
  const { toasts, dismiss } = useToastState()

  if (toasts.length === 0) return null

  return (
    <div
      className="fixed bottom-4 right-4 z-[100] flex flex-col gap-2 w-80"
      role="region"
      aria-label="Notifications"
    >
      {toasts.map((t) => (
        <div
          key={t.id}
          className={`
            rounded-lg border px-4 py-3 shadow-lg
            animate-in slide-in-from-right-full fade-in
            ${variantClasses[t.variant]}
          `}
          role="alert"
        >
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium">{t.title}</p>
              {t.description && (
                <p className="text-xs opacity-80 mt-0.5">{t.description}</p>
              )}
            </div>
            <button
              onClick={() => dismiss(t.id)}
              className="shrink-0 opacity-60 hover:opacity-100 transition-opacity"
              aria-label="Dismiss"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      ))}
    </div>
  )
}
