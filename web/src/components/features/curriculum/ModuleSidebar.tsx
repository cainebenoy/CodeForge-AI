'use client'

import {
  Check,
  Clock,
  Star,
  Rocket,
  FolderArchive,
  Circle,
  ListChecks,
} from 'lucide-react'
import type { LearningModule } from '@/types/api.types'
import type { StudentProgress } from '@/types/api.types'

/* ─── Types ─── */
interface Objective {
  label: string
  sublabel?: string
  status: 'completed' | 'active' | 'pending'
}

const darkObjectives: Objective[] = [
  { label: 'Understanding JSX syntax', status: 'completed' },
  { label: 'Components and Props', status: 'active' },
  { label: 'State and Lifecycle', status: 'pending' },
  { label: 'Handling Events', status: 'pending' },
]

const lightObjectives: Objective[] = [
  { label: 'Grid Container & Items', sublabel: 'Defining the grid context', status: 'completed' },
  { label: 'Grid Template Columns', sublabel: 'fr units, repeat(), and minmax()', status: 'active' },
  { label: 'Grid Areas', sublabel: 'Named template areas', status: 'pending' },
  { label: 'Implicit Grids', sublabel: 'Auto-placement algorithms', status: 'pending' },
]

export interface ModuleSidebarProps {
  /** API module data; falls back to demo */
  module?: LearningModule
  /** Index of the current module */
  moduleIndex?: number
  /** Active project ID */
  projectId?: string
  /** Student progress data */
  progress?: StudentProgress
  /** Called when Launch Lab is clicked */
  onLaunchLab?: () => void
}

/**
 * ModuleSidebar — Right sidebar showing module details for
 * the currently-selected skill tree node.
 *
 * **Dark**: Glassmorphism panel — synopsis, stats grid, objectives with
 *           check-circles, resources card, "Launch Lab Environment" CTA.
 * **Light**: White panel — module/level badges, title, stats row,
 *            objectives list, prerequisites, "LAUNCH LAB" CTA.
 */
export function ModuleSidebar({
  module,
  moduleIndex = 0,
  projectId,
  progress,
  onLaunchLab,
}: ModuleSidebarProps) {
  // Derive objectives from API module steps, or use demo data
  const derivedDarkObjectives: Objective[] = module?.steps
    ? module.steps.map((step, i) => ({
        label: step.title,
        status: i < (progress?.completed_modules ?? 0)
          ? 'completed' as const
          : i === (progress?.current_module ?? 0)
            ? 'active' as const
            : 'pending' as const,
      }))
    : darkObjectives

  const derivedLightObjectives: Objective[] = module?.steps
    ? module.steps.map((step, i) => ({
        label: step.title,
        sublabel: step.description,
        status: i < (progress?.completed_modules ?? 0)
          ? 'completed' as const
          : i === (progress?.current_module ?? 0)
            ? 'active' as const
            : 'pending' as const,
      }))
    : lightObjectives

  const moduleTitle = module?.title ?? 'React Foundations'
  const moduleDesc = module?.description ?? 'Frontend Engineering • Unit 3'
  const estimatedTime = module?.estimated_hours
    ? `${Math.floor(module.estimated_hours)}h ${Math.round((module.estimated_hours % 1) * 60)}m`
    : '2h 45m'
  return (
    <>
      {/* ── Dark sidebar ── */}
      <aside className="hidden dark:flex w-[380px] h-full bg-zinc-950/80 backdrop-blur-xl border-l border-border/30 flex-col shadow-2xl z-20 shrink-0">
        {/* Header */}
        <div className="p-6 border-b border-border/20">
          <div className="flex items-center gap-2 mb-2">
            <div className="h-2 w-2 rounded-full bg-violet-400 animate-pulse" />
            <span className="text-xs font-mono text-violet-400 uppercase tracking-wider">
              Current Module
            </span>
          </div>
          <h2 className="text-2xl font-bold text-foreground mb-1">
            {moduleTitle}
          </h2>
          <p className="text-muted-foreground text-sm">
            {moduleDesc}
          </p>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-6 space-y-8">
          {/* Synopsis */}
          <div className="space-y-3">
            <h3 className="text-sm font-mono text-muted-foreground uppercase tracking-widest font-semibold">
              Synopsis
            </h3>
            <p className="text-zinc-300 text-sm leading-relaxed">
              Master the fundamentals of React&apos;s component-based
              architecture. Learn how to compose complex UIs from small,
              isolated pieces of code called &quot;components&quot;.
            </p>
          </div>

          {/* Stats grid */}
          <div className="grid grid-cols-2 gap-3">
            <div className="bg-zinc-900/50 border border-border/30 rounded-lg p-3">
              <div className="flex items-center gap-2 text-muted-foreground mb-1">
                <Clock className="size-4" />
                <span className="text-xs font-medium">Est. Time</span>
              </div>
              <span className="text-foreground font-mono font-bold">{estimatedTime}</span>
            </div>
            <div className="bg-zinc-900/50 border border-border/30 rounded-lg p-3">
              <div className="flex items-center gap-2 text-muted-foreground mb-1">
                <Star className="size-4" />
                <span className="text-xs font-medium">XP Reward</span>
              </div>
              <span className="text-cf-primary font-mono font-bold">+350 XP</span>
            </div>
          </div>

          {/* Objectives */}
          <div className="space-y-4">
            <h3 className="text-sm font-mono text-muted-foreground uppercase tracking-widest font-semibold">
              Objectives
            </h3>
            <div className="space-y-3">
              {derivedDarkObjectives.map((obj) => (
                <div key={obj.label} className="flex gap-3 items-start">
                  <div
                    className={`mt-0.5 size-5 rounded-full flex items-center justify-center shrink-0 ${
                      obj.status === 'completed'
                        ? 'border border-cf-primary/30 bg-cf-primary/10 text-cf-primary'
                        : 'border border-border bg-muted/20 text-transparent'
                    }`}
                  >
                    <Check className="size-3.5" strokeWidth={3} />
                  </div>
                  <span
                    className={`text-sm ${
                      obj.status === 'completed'
                        ? 'text-muted-foreground line-through decoration-zinc-600'
                        : 'text-zinc-300'
                    }`}
                  >
                    {obj.label}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Resources card */}
          <div className="p-4 rounded-lg bg-zinc-900 border border-border/30 flex items-start gap-4">
            <div className="size-10 rounded bg-indigo-500/10 flex items-center justify-center text-indigo-400 shrink-0">
              <FolderArchive className="size-5" />
            </div>
            <div>
              <h4 className="text-sm font-bold text-foreground">Starter Files</h4>
              <p className="text-xs text-muted-foreground mt-1">
                Download the initial project setup to begin the lab exercises.
              </p>
              <button className="inline-block mt-2 text-xs text-indigo-400 hover:text-indigo-300 font-medium">
                Download .zip (2.4MB)
              </button>
            </div>
          </div>
        </div>

        {/* Footer CTA */}
        <div className="p-6 border-t border-border/30 bg-zinc-950">
          <button
            onClick={onLaunchLab}
            className="w-full h-12 bg-cf-primary hover:brightness-110 text-black font-bold rounded-lg flex items-center justify-center gap-2 transition-all shadow-[0_0_20px_rgba(19,236,109,0.2)] hover:shadow-[0_0_30px_rgba(19,236,109,0.4)]"
          >
            <Rocket className="size-5" />
            Launch Lab Environment
          </button>
          <div className="mt-3 text-center">
            <span className="text-xs text-muted-foreground">Last attempt: 2 days ago</span>
          </div>
        </div>
      </aside>

      {/* ── Light sidebar ── */}
      <aside className="flex dark:hidden w-[360px] bg-white border-l border-border shadow-xl z-30 flex-col">
        {/* Header */}
        <div className="p-6 border-b border-border/50">
          <div className="flex items-center gap-2 mb-2">
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-violet-600/10 text-violet-600 uppercase tracking-wider">
              Module {(moduleIndex ?? 0) + 1}
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-700 uppercase tracking-wider">
              Intermediate
            </span>
          </div>
          <h2 className="text-2xl font-bold text-foreground leading-tight">
            {moduleTitle}
          </h2>
          <p className="text-sm text-muted-foreground mt-2">
            {moduleDesc}
          </p>
        </div>

        {/* Stats row */}
        <div className="grid grid-cols-2 border-b border-border/50 divide-x divide-border/50">
          <div className="p-4 flex flex-col gap-1 items-center text-center">
            <span className="text-xs text-muted-foreground uppercase tracking-wider font-medium">
              Est. Time
            </span>
            <span className="text-base font-bold text-foreground">2 Hours</span>
          </div>
          <div className="p-4 flex flex-col gap-1 items-center text-center">
            <span className="text-xs text-muted-foreground uppercase tracking-wider font-medium">
              XP Reward
            </span>
            <span className="text-base font-bold text-violet-600">500 XP</span>
          </div>
        </div>

        {/* Objectives */}
        <div className="flex-1 overflow-y-auto p-6">
          <h3 className="text-sm font-bold text-foreground uppercase tracking-wide mb-4 flex items-center gap-2">
            <ListChecks className="size-4" />
            Objectives
          </h3>
          <ul className="space-y-3">
            {derivedLightObjectives.map((obj) => (
              <li key={obj.label} className="flex items-start gap-3 group">
                <div className="mt-0.5">
                  {obj.status === 'completed' && (
                    <Check className="size-4 text-emerald-500" />
                  )}
                  {obj.status === 'active' && (
                    <div className="size-4 rounded-full border-2 border-violet-600 animate-pulse" />
                  )}
                  {obj.status === 'pending' && (
                    <Circle className="size-4 text-muted-foreground/30" />
                  )}
                </div>
                <div className={obj.status === 'pending' ? 'opacity-60' : ''}>
                  <span
                    className={`text-sm font-medium block transition-colors ${
                      obj.status === 'completed'
                        ? 'text-muted-foreground'
                        : obj.status === 'active'
                          ? 'text-foreground font-bold group-hover:text-violet-600'
                          : 'text-muted-foreground'
                    }`}
                  >
                    {obj.label}
                  </span>
                  {obj.sublabel && (
                    <span className="text-xs text-muted-foreground">{obj.sublabel}</span>
                  )}
                </div>
              </li>
            ))}
          </ul>

          {/* Prerequisites */}
          <div className="mt-8 p-4 bg-muted/50 rounded border border-border">
            <h4 className="text-xs font-bold text-foreground uppercase mb-2">
              Prerequisites
            </h4>
            <div className="flex gap-2 flex-wrap">
              {['HTML Structure', 'CSS Box Model'].map((p) => (
                <span
                  key={p}
                  className="text-xs bg-white border border-border px-2 py-1 rounded text-muted-foreground"
                >
                  {p}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Footer CTA */}
        <div className="p-6 border-t border-border bg-muted/30">
          <button
            onClick={onLaunchLab}
            className="w-full bg-foreground hover:bg-foreground/90 text-white font-bold py-3.5 px-4 rounded-sm flex items-center justify-center gap-2 transition-all shadow-lg hover:shadow-xl active:scale-[0.98]"
          >
            <Rocket className="size-5" />
            LAUNCH LAB
          </button>
          <p className="text-[10px] text-center text-muted-foreground mt-2">
            Last accessed 2 hours ago
          </p>
        </div>
      </aside>
    </>
  )
}
