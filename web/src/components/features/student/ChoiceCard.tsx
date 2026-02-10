'use client'

import {
  Zap,
  Flame,
  Database,
  CheckCircle,
  Layers,
  BellRing,
  GitBranch,
  Check,
} from 'lucide-react'
import type { ReactNode } from 'react'

/* ─── Types ─── */
export interface ChoiceOption {
  id: string
  title: string
  description: string
  /** Lucide icon key */
  icon: 'bolt' | 'flame' | 'database' | 'layers' | 'bell' | 'git'
  features: string[]
  /** Dark-mode specific */
  badge?: string
  badgeVariant?: 'recommended' | 'fast' | 'hard'
  xpLabel?: string
  xpAmount?: string
  difficulty?: string
  difficultyPercent?: number
  /** Light-mode selected state */
  selected?: boolean
  recommended?: boolean
  /** Accent colour token (Tailwind class fragment) */
  accent?: string
}

const iconMap: Record<string, ReactNode> = {
  bolt: <Zap className="size-5" />,
  flame: <Flame className="size-5" />,
  database: <Database className="size-5" />,
  layers: <Layers className="size-5" />,
  bell: <BellRing className="size-5" />,
  git: <GitBranch className="size-5" />,
}

/* ─── Badge colours by variant ─── */
const badgeStyles: Record<string, string> = {
  recommended:
    'bg-cf-primary text-black dark:bg-cf-primary dark:text-[#102218]',
  fast: 'bg-muted text-muted-foreground dark:bg-gray-700 dark:text-gray-200 dark:border dark:border-gray-600',
  hard: 'bg-muted text-destructive dark:bg-[#1a1a1a] dark:text-red-400 dark:border dark:border-red-900',
}

const accentMap: Record<string, { text: string; bg: string; bar: string }> = {
  primary: {
    text: 'text-cf-primary',
    bg: 'bg-cf-primary/20',
    bar: 'bg-cf-primary',
  },
  orange: {
    text: 'text-orange-400',
    bg: 'bg-orange-500/20',
    bar: 'bg-orange-400',
  },
  red: { text: 'text-red-400', bg: 'bg-red-500/20', bar: 'bg-red-500' },
}

/**
 * ChoiceCard — A single option in the Student Choice Framework.
 *
 * **Dark mode**: Game-like card with XP reward, difficulty bar, glow on recommended.
 * **Light mode**: Clean paper card; selected card gets purple border + checkmark.
 */
export function ChoiceCard({
  option,
  onSelect,
}: {
  option: ChoiceOption
  onSelect?: (id: string) => void
}) {
  const accent = accentMap[option.accent ?? 'primary'] ?? accentMap.primary
  const isRecommended = option.badgeVariant === 'recommended' || option.recommended
  const isSelected = option.selected

  return (
    <div
      onClick={() => onSelect?.(option.id)}
      className={`
        group relative flex flex-col rounded-xl p-6 cursor-pointer transition-all duration-200 h-full
        ${
          /* ── Dark mode styles ── */
          isRecommended
            ? 'dark:bg-secondary/50 dark:border-2 dark:border-cf-primary dark:shadow-[0_0_20px_rgba(19,236,109,0.15)] dark:hover:shadow-[0_0_30px_rgba(19,236,109,0.25)]'
            : 'dark:bg-secondary/30 dark:border dark:border-border dark:hover:bg-secondary/50 dark:hover:border-muted-foreground/30'
        }
        ${
          /* ── Light mode styles ── */
          isSelected
            ? 'bg-violet-50 border-2 border-violet-600 shadow-lg scale-[1.02] md:scale-105 z-10'
            : 'bg-white border-2 border-border hover:border-muted-foreground/50 hover:shadow-md'
        }
      `}
    >
      {/* Badge */}
      {option.badge && (
        <div
          className={`absolute -top-3 left-1/2 -translate-x-1/2 text-[10px] font-bold uppercase tracking-wider px-3 py-1 rounded-full shadow-sm
            ${badgeStyles[option.badgeVariant ?? 'recommended']}
            ${isSelected ? 'ring-4 ring-white' : ''}
          `}
        >
          {option.badge}
        </div>
      )}

      {/* Icon + title row */}
      <div className="mb-5 flex items-center justify-between mt-2">
        {/* Icon */}
        <div
          className={`w-12 h-12 rounded-lg flex items-center justify-center transition-all
            ${
              isSelected
                ? 'bg-white border border-violet-200 shadow-sm'
                : isRecommended
                  ? `${accent.bg} dark:${accent.bg}`
                  : 'bg-muted border border-border group-hover:bg-background group-hover:border-muted-foreground/30'
            }
          `}
        >
          <span
            className={
              isSelected
                ? 'text-foreground'
                : isRecommended
                  ? accent.text
                  : 'text-muted-foreground group-hover:text-foreground transition-colors'
            }
          >
            {iconMap[option.icon]}
          </span>
        </div>

        {/* Light-mode checkmark */}
        {isSelected && (
          <div className="size-6 rounded-full bg-violet-600 flex items-center justify-center shadow-sm dark:hidden">
            <Check className="size-3.5 text-white" />
          </div>
        )}
      </div>

      {/* Content */}
      <div className="mt-auto">
        <h3
          className={`text-xl font-bold mb-2 transition-colors
            ${
              isSelected
                ? 'text-violet-700 dark:text-white'
                : isRecommended
                  ? 'text-foreground'
                  : 'text-muted-foreground group-hover:text-foreground dark:text-muted-foreground dark:group-hover:text-white'
            }
          `}
        >
          {option.title}
        </h3>
        <p
          className={`text-sm leading-relaxed transition-colors
            ${
              isSelected
                ? 'text-foreground/80 font-medium'
                : 'text-muted-foreground group-hover:text-foreground/70'
            }
          `}
        >
          {option.description}
        </p>

        {/* Feature checks (dark mode) */}
        <div className="mt-3 space-y-1.5 hidden dark:block">
          {option.features.map((f) => (
            <div
              key={f}
              className={`flex items-center gap-2 text-xs ${
                isRecommended
                  ? `${accent.text}/80`
                  : 'text-muted-foreground group-hover:text-muted-foreground/80'
              }`}
            >
              <CheckCircle className="size-3.5" />
              <span>{f}</span>
            </div>
          ))}
        </div>
      </div>

      {/* XP / Difficulty footer (dark mode only) */}
      {option.xpAmount && (
        <div className="pt-4 border-t border-border/30 mt-6 hidden dark:block">
          <div className="flex justify-between items-center text-xs font-mono mb-2">
            <span className="text-muted-foreground">{option.xpLabel ?? 'XP Reward'}</span>
            <span className={`${accent.text} font-bold`}>{option.xpAmount}</span>
          </div>
          <div className="w-full bg-muted/30 rounded-full h-1.5">
            <div
              className={`${accent.bar} h-1.5 rounded-full transition-all`}
              style={{ width: `${option.difficultyPercent ?? 50}%` }}
            />
          </div>
          <div className="mt-2 text-[10px] text-muted-foreground/60 text-right">
            Difficulty: {option.difficulty ?? 'Moderate'}
          </div>
        </div>
      )}
    </div>
  )
}
