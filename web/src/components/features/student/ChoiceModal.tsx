'use client'

import { useState } from 'react'
import {
  ArrowRight,
  ArrowLeft,
  Lock,
  X,
  Route,
  Loader2,
} from 'lucide-react'
import { ChoiceCard, type ChoiceOption } from './ChoiceCard'

/* ─── Demo data: Dark mode (Database Architecture) ─── */
const darkChoices: ChoiceOption[] = [
  {
    id: 'supabase',
    title: 'Supabase',
    description:
      'Open source Firebase alternative. Gives you a Postgres database, Authentication, instant APIs, and Realtime subscriptions.',
    icon: 'bolt',
    features: ['Relational Data (SQL)', 'Built-in Auth UI'],
    badge: 'Recommended',
    badgeVariant: 'recommended',
    accent: 'primary',
    xpLabel: 'XP Reward',
    xpAmount: '+50 Arch XP',
    difficulty: 'Moderate',
    difficultyPercent: 40,
  },
  {
    id: 'firebase',
    title: 'Firebase',
    description:
      'Backed by Google. Excellent for rapid development with NoSQL document stores. Great for mobile apps.',
    icon: 'flame',
    features: ['NoSQL Documents', 'Simple SDKs'],
    badge: 'Fast Prototyping',
    badgeVariant: 'fast',
    accent: 'orange',
    xpLabel: 'XP Reward',
    xpAmount: '+30 Speed XP',
    difficulty: 'Easy',
    difficultyPercent: 25,
  },
  {
    id: 'raw-sql',
    title: 'Raw SQL',
    description:
      'Manual configuration. Write your own migrations and queries. Maximum control but steeper learning curve.',
    icon: 'database',
    features: ['Full Control', 'Deep Understanding'],
    badge: 'Hard Mode',
    badgeVariant: 'hard',
    accent: 'red',
    xpLabel: 'XP Reward',
    xpAmount: '+150 Knowledge XP',
    difficulty: 'Expert',
    difficultyPercent: 90,
  },
]

/* ─── Demo data: Light mode (Architecture Strategy) ─── */
const lightChoices: ChoiceOption[] = [
  {
    id: 'mvc',
    title: 'Model-View-Controller',
    description: 'Separates concerns into three interconnected components.',
    icon: 'layers',
    features: [],
  },
  {
    id: 'observer',
    title: 'Observer Pattern',
    description:
      'Define a subscription mechanism to notify multiple objects.',
    icon: 'bell',
    features: [],
    badge: 'Recommended',
    badgeVariant: 'recommended',
    recommended: true,
    selected: true,
  },
  {
    id: 'flux',
    title: 'Flux Architecture',
    description:
      'Unidirectional data flow for predictable state management.',
    icon: 'git',
    features: [],
  },
]

export interface ChoiceModalProps {
  /** Project ID for context */
  projectId?: string
  /** API-sourced options; falls back to demo data */
  apiOptions?: ChoiceOption[]
  /** Custom title from API; overrides default */
  title?: string
  /** Called with selected option ID on confirm */
  onConfirm?: (optionId: string) => void
  /** Called on cancel */
  onCancel?: () => void
  /** Disable buttons while submitting */
  isSubmitting?: boolean
}

/**
 * ChoiceModal — Full "Choice Framework" overlay used in Student Mode.
 *
 * Accepts real API data via `apiOptions` prop, falling back to built-in demo data.
 *
 * **Dark**: glass panel with XP/difficulty, "Confirm Selection" CTA.
 * **Light**: white paper card with progress stepper, "Lock in Choice" CTA.
 */
export function ChoiceModal({
  projectId,
  apiOptions,
  title,
  onConfirm,
  onCancel,
  isSubmitting = false,
}: ChoiceModalProps) {
  // Use API data if available, otherwise demo data
  // Unified demo data (preferring the detailed "Dark Mode" set as it has more info)
  const choices = apiOptions ?? darkChoices

  const [selected, setSelected] = useState<string>(choices[0]?.id ?? 'supabase')

  const handleConfirm = () => {
    onConfirm?.(selected)
  }

  return (
    <div className="w-full max-w-5xl flex flex-col overflow-hidden
                    bg-white dark:bg-black/60 dark:backdrop-blur-xl
                    rounded-2xl shadow-2xl border border-border">

      {/* ─── Header ─── */}
      <div className="px-8 pt-10 pb-4 sm:px-12 relative">
        
        {/* Icon badge */}
        <div className="text-center mb-4">
          <div className="inline-flex items-center justify-center p-3 rounded-full bg-violet-100 dark:bg-cf-primary/10 border border-violet-200 dark:border-cf-primary/20">
            <Route className="size-7 text-violet-600 dark:text-cf-primary" />
          </div>
        </div>

        {/* Title / subtitle */}
        <div className="text-center max-w-3xl mx-auto">
            <h1 className="text-3xl md:text-4xl font-bold text-foreground mb-2 tracking-tight">
              {title ?? 'Choose your Database Architecture'}
            </h1>
            <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
              Select the backend infrastructure that best fits your project goals. This decision will shape your code structure.
            </p>
        </div>
      </div>

      {/* ─── Cards grid ─── */}
      <div className="px-8 py-4 sm:px-12 flex-grow">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {choices.map((opt) => (
            <ChoiceCard
              key={opt.id}
              option={{ 
                ...opt, 
                selected: opt.id === selected, 
                recommended: opt.badgeVariant === 'recommended' 
              }}
              onSelect={setSelected}
            />
          ))}
        </div>
      </div>

      {/* ─── Footer ─── */}
      <div className="flex p-6 border-t border-border/30 bg-muted/30 dark:bg-secondary/50 justify-between sm:justify-end gap-4 items-center">
        <span className="text-xs text-muted-foreground font-mono hidden sm:inline-block mr-auto">
          ARCH_ID: 884-2A-DB-SELECT
        </span>
        <button
          onClick={onCancel}
          className="px-6 py-2.5 rounded-lg border border-border text-foreground font-medium hover:bg-muted transition-colors text-sm"
        >
          Cancel
        </button>
        <button
          onClick={handleConfirm}
          disabled={isSubmitting}
          className="px-8 py-2.5 rounded-lg bg-violet-600 dark:bg-cf-primary text-white dark:text-black font-bold shadow-lg hover:brightness-110 transition-all text-sm flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isSubmitting ? <Loader2 className="size-4 animate-spin" /> : null}
          Confirm Selection
          {!isSubmitting && <ArrowRight className="size-4" />}
        </button>
      </div>
    </div>
  )
}