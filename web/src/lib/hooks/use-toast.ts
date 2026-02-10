'use client'

import { useState, useCallback } from 'react'

export type ToastVariant = 'default' | 'success' | 'error' | 'warning'

export interface Toast {
  id: string
  title: string
  description?: string
  variant: ToastVariant
}

/** Max toasts visible at once */
const MAX_TOASTS = 5
/** Auto-dismiss duration in ms */
const DISMISS_DELAY = 4000

let toastCounter = 0

/**
 * Lightweight toast state manager.
 * Used by the <Toaster /> component in the layout.
 */

// Global listeners so any component can trigger a toast
type Listener = (toast: Toast) => void
const listeners = new Set<Listener>()

function notifyListeners(toast: Toast) {
  listeners.forEach((fn) => fn(toast))
}

/** Dispatch a toast from anywhere (including non-component code) */
export function toast(opts: Omit<Toast, 'id'>) {
  const t: Toast = { ...opts, id: `toast-${++toastCounter}` }
  notifyListeners(t)
  return t.id
}

/** Convenience helpers */
toast.success = (title: string, description?: string) =>
  toast({ title, description, variant: 'success' })
toast.error = (title: string, description?: string) =>
  toast({ title, description, variant: 'error' })
toast.warning = (title: string, description?: string) =>
  toast({ title, description, variant: 'warning' })

/**
 * React hook that powers the <Toaster /> component.
 * Manages the visible toast queue and auto-dismiss timers.
 */
export function useToastState() {
  const [toasts, setToasts] = useState<Toast[]>([])

  const addToast = useCallback((t: Toast) => {
    setToasts((prev) => [...prev, t].slice(-MAX_TOASTS))

    // Auto-dismiss
    setTimeout(() => {
      setToasts((prev) => prev.filter((x) => x.id !== t.id))
    }, DISMISS_DELAY)
  }, [])

  const dismiss = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  // Register this hook as a global listener
  useState(() => {
    listeners.add(addToast)
    return () => listeners.delete(addToast)
  })

  return { toasts, dismiss }
}
