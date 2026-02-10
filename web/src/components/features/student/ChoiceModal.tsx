'use client'

import { useState } from 'react'
import {
  ArrowRight,
  ArrowLeft,
  Lock,
  X,
  Route,
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

/**
 * ChoiceModal — Full "Choice Framework" overlay used in Student Mode.
 *
 * **Dark**: glass panel with XP/difficulty, "Confirm Selection" CTA.
 * **Light**: white paper card with progress stepper, "Lock in Choice" CTA.
 */
export function ChoiceModal() {
  const [darkSelected, setDarkSelected] = useState<string>('supabase')
  const [lightSelected, setLightSelected] = useState<string>('observer')

  return (
    <div className="w-full max-w-5xl flex flex-col overflow-hidden
                    dark:glass-panel dark:rounded-xl dark:shadow-2xl dark:shadow-black/50
                    bg-white rounded-2xl shadow-[0_25px_50px_-12px_rgba(0,0,0,0.15)] border border-border dark:border-transparent">

      {/* ─── Header ─── */}
      <div className="px-8 pt-10 pb-4 sm:px-12 relative">
        {/* Light-mode progress stepper */}
        <div className="flex items-center justify-between gap-4 mb-8 dark:hidden">
          <div className="flex items-center gap-2">
            <span className="flex items-center justify-center w-6 h-6 rounded-full bg-violet-600 text-white text-xs font-bold">
              4
            </span>
            <span className="text-xs font-bold text-muted-foreground tracking-wider uppercase">
              Pattern Selection
            </span>
          </div>
          <div className="h-1.5 flex-1 max-w-xs bg-muted rounded-full overflow-hidden">
            <div className="h-full bg-violet-600 rounded-full" style={{ width: '65%' }} />
          </div>
          <span className="text-xs font-medium text-muted-foreground">Step 4 of 6</span>
        </div>

        {/* Dark-mode icon badge */}
        <div className="text-center hidden dark:block mb-4">
          <div className="inline-flex items-center justify-center p-3 rounded-full bg-cf-primary/10 border border-cf-primary/20">
            <Route className="size-7 text-cf-primary" />
          </div>
        </div>

        {/* Title / subtitle */}
        <div className="flex justify-between items-start gap-4">
          <div className="max-w-3xl dark:text-center dark:mx-auto">
            {/* Dark title */}
            <h1 className="hidden dark:block text-3xl md:text-4xl font-bold text-white mb-2 tracking-tight">
              Choose your Database Architecture
            </h1>
            <p className="hidden dark:block text-muted-foreground text-lg max-w-2xl mx-auto">
              Select the backend infrastructure that best fits your project goals. This decision will shape your code structure.
            </p>
            {/* Light title */}
            <h1 className="dark:hidden text-3xl sm:text-4xl font-bold text-foreground tracking-tight mb-3">
              Select Architecture Strategy
            </h1>
            <p className="dark:hidden text-lg text-muted-foreground font-light leading-relaxed">
              Which pattern best solves the data flow problem in this module?
            </p>
          </div>

          {/* Light-mode close button */}
          <button
            className="hidden sm:flex dark:hidden items-center justify-center size-10 rounded-full hover:bg-muted transition-colors group"
            aria-label="Close modal"
          >
            <X className="size-5 text-muted-foreground group-hover:text-foreground" />
          </button>
        </div>
      </div>

      {/* ─── Cards grid ─── */}
      <div className="px-8 py-4 sm:px-12 flex-grow">
        {/* Dark-mode cards */}
        <div className="hidden dark:grid grid-cols-1 md:grid-cols-3 gap-6">
          {darkChoices.map((opt) => (
            <ChoiceCard
              key={opt.id}
              option={{ ...opt, selected: opt.id === darkSelected, recommended: opt.badgeVariant === 'recommended' }}
              onSelect={setDarkSelected}
            />
          ))}
        </div>

        {/* Light-mode cards */}
        <div className="grid dark:hidden grid-cols-1 md:grid-cols-3 gap-6">
          {lightChoices.map((opt) => (
            <ChoiceCard
              key={opt.id}
              option={{ ...opt, selected: opt.id === lightSelected }}
              onSelect={setLightSelected}
            />
          ))}
        </div>
      </div>

      {/* ─── Footer ─── */}
      {/* Dark footer */}
      <div className="hidden dark:flex p-6 border-t border-border/30 bg-secondary/50 justify-end gap-4 items-center">
        <span className="text-xs text-muted-foreground font-mono hidden sm:inline-block">
          ARCH_ID: 884-2A-DB-SELECT
        </span>
        <button className="px-6 py-2.5 rounded-lg border border-border text-foreground font-medium hover:bg-muted transition-colors text-sm">
          Cancel
        </button>
        <button className="px-8 py-2.5 rounded-lg bg-cf-primary text-black font-bold shadow-[0_0_15px_rgba(19,236,109,0.4)] hover:shadow-[0_0_25px_rgba(19,236,109,0.6)] hover:brightness-110 transition-all text-sm flex items-center gap-2">
          Confirm Selection
          <ArrowRight className="size-4" />
        </button>
      </div>

      {/* Light footer */}
      <div className="flex dark:hidden px-8 py-8 sm:px-12 mt-4 bg-muted/30 border-t border-border flex-col-reverse sm:flex-row items-center justify-between gap-6">
        <button className="text-muted-foreground hover:text-foreground font-medium text-sm transition-colors flex items-center gap-2 group">
          <ArrowLeft className="size-4 group-hover:-translate-x-1 transition-transform" />
          Review Lesson Material
        </button>
        <div className="flex items-center gap-4 w-full sm:w-auto">
          <button className="hidden sm:block text-muted-foreground hover:bg-muted px-6 py-3 rounded-lg font-semibold transition-colors">
            Cancel
          </button>
          <button className="w-full sm:w-auto bg-violet-600 hover:bg-violet-700 text-white px-8 py-3 rounded-lg font-bold shadow-lg shadow-violet-600/25 transition-all active:scale-[0.98] flex items-center justify-center gap-2">
            <Lock className="size-4" />
            Lock in Choice
          </button>
        </div>
      </div>
    </div>
  )
}