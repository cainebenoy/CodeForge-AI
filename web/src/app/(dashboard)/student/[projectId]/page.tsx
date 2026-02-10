'use client'

import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { ChoiceModal } from '@/components/features/student'
import { useChoiceFramework, useSelectChoice, useStudentProgress } from '@/lib/hooks/use-student'
import { useProject } from '@/lib/hooks/use-project'
import { Loader2 } from 'lucide-react'
import {
  Code2,
  MoreHorizontal,
  Database as DbIcon,
  FileCode,
} from 'lucide-react'
import type { ChoiceOption } from '@/components/features/student'

/**
 * Student Choice page — overlay modal for architecture / pattern decisions.
 *
 * Fetches choice framework from the API when a decision context is provided,
 * falls back to demo data in the ChoiceModal when API data is unavailable.
 */
export default function StudentProjectPage({
  params,
}: {
  params: { projectId: string }
}) {
  const router = useRouter()
  const { data: project } = useProject(params.projectId)
  const { data: progress } = useStudentProgress(params.projectId)
  const choiceFramework = useChoiceFramework(params.projectId)
  const selectChoice = useSelectChoice(params.projectId)

  const [choiceData, setChoiceData] = useState<{
    context: string
    options: ChoiceOption[]
    recommendation?: string
  } | null>(null)

  // Map API ImplementationOption[] → UI ChoiceOption[]
  const mapApiOptions = useCallback(
    (apiOptions: Array<{
      id: string; title: string; description: string;
      difficulty: string; pros: string[]; cons: string[];
      estimated_time: string;
    }>, recommendation?: string): ChoiceOption[] => {
      const iconPool: Array<'bolt' | 'flame' | 'database' | 'layers' | 'bell' | 'git'> =
        ['bolt', 'flame', 'database', 'layers', 'bell', 'git']
      const accentPool = ['primary', 'orange', 'red']

      return apiOptions.map((opt, i) => {
        const isRecommended = recommendation === opt.id
        return {
          id: opt.id,
          title: opt.title,
          description: opt.description,
          icon: iconPool[i % iconPool.length],
          features: opt.pros.slice(0, 3),
          badge: isRecommended ? 'Recommended' : undefined,
          badgeVariant: isRecommended ? 'recommended' as const : undefined,
          accent: accentPool[i % accentPool.length],
          xpLabel: 'Est. Time',
          xpAmount: opt.estimated_time,
          difficulty: opt.difficulty,
          difficultyPercent: opt.difficulty === 'beginner' ? 25
            : opt.difficulty === 'intermediate' ? 50
            : opt.difficulty === 'advanced' ? 75 : 90,
        }
      })
    },
    [],
  )

  const handleSelect = useCallback(
    async (optionId: string) => {
      const moduleIndex = progress?.current_module ?? 0
      selectChoice.mutate(
        { module_index: moduleIndex, option_id: optionId },
        {
          onSuccess: () => {
            router.push(`/lab/${params.projectId}`)
          },
        },
      )
    },
    [selectChoice, progress, params.projectId, router],
  )

  const handleCancel = useCallback(() => {
    router.push(`/curriculum`)
  }, [router])

  return (
    <div className="relative h-screen overflow-hidden bg-background text-foreground flex flex-col">
      {/* ════════════════════════════════════════════════
          DARK-MODE BACKGROUND — dimmed & non-interactive
         ════════════════════════════════════════════════ */}
      <div className="hidden dark:flex flex-col h-full">
        {/* Dimmed top nav */}
        <header className="flex items-center justify-between px-6 py-3 border-b border-border bg-secondary opacity-40 pointer-events-none select-none">
          <div className="flex items-center gap-4">
            <div className="size-6 text-cf-primary">
              <Code2 className="size-6" />
            </div>
            <h2 className="text-foreground text-lg font-bold tracking-tight">
              CodeForge AI
            </h2>
          </div>
          <div className="flex items-center gap-9">
            {['Dashboard', 'Curriculum', 'Projects'].map((l) => (
              <span key={l} className="text-sm font-medium text-foreground opacity-60">
                {l}
              </span>
            ))}
            <div className="size-10 rounded-full bg-muted" />
          </div>
        </header>

        {/* Dimmed main: mentor chat + code preview */}
        <div className="flex flex-1 min-h-0">
          {/* Mentor Chat pane */}
          <div className="w-1/3 border-r border-border bg-secondary flex flex-col opacity-20 pointer-events-none select-none">
            <div className="p-4 border-b border-border flex justify-between items-center">
              <h3 className="font-bold text-lg text-foreground">Mentor Chat</h3>
              <MoreHorizontal className="size-5 text-muted-foreground" />
            </div>
            <div className="flex-1 p-4 flex flex-col gap-6 overflow-hidden">
              {/* AI bubble */}
              <div className="flex items-end gap-3">
                <div className="size-8 shrink-0 rounded-full bg-muted" />
                <div className="bg-muted p-3 rounded-lg rounded-bl-none max-w-[85%]">
                  <p className="text-sm text-muted-foreground">
                    Hello Alex! We&apos;ve reached a pivotal moment in your
                    e-commerce project. It&apos;s time to decide how we&apos;ll
                    store your data.
                  </p>
                </div>
              </div>
              {/* User bubble */}
              <div className="flex items-end gap-3 justify-end">
                <div className="bg-cf-primary/20 p-3 rounded-lg rounded-br-none max-w-[85%] text-right">
                  <p className="text-sm text-foreground/80">
                    I&apos;ve been reading about SQL vs NoSQL. What do you think
                    is best for a beginner?
                  </p>
                </div>
                <div className="size-8 shrink-0 rounded-full bg-muted" />
              </div>
              {/* AI reply */}
              <div className="flex items-end gap-3">
                <div className="size-8 shrink-0 rounded-full bg-muted" />
                <div className="bg-muted p-3 rounded-lg rounded-bl-none max-w-[85%]">
                  <p className="text-sm text-muted-foreground">
                    That depends on your goals. I&apos;ve prepared a &quot;Choice
                    Framework&quot; for you to visualize the trade-offs.
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Code editor pane */}
          <div className="flex-1 bg-black flex flex-col opacity-20 pointer-events-none select-none">
            {/* Tabs */}
            <div className="h-10 border-b border-border flex items-center px-4 gap-4 bg-secondary">
              <div className="flex items-center gap-2 px-3 py-1 bg-muted rounded-t border-t border-x border-border text-xs text-cf-primary">
                <DbIcon className="size-3.5" />
                schema.design
              </div>
              <div className="flex items-center gap-2 px-3 py-1 text-xs text-muted-foreground">
                <FileCode className="size-3.5" />
                server.js
              </div>
            </div>
            {/* Code lines */}
            <div className="flex-1 p-6 font-mono text-sm overflow-hidden">
              {[
                { n: 1, code: '// Waiting for architecture decision...',  cls: 'text-muted-foreground' },
                { n: 2, code: '' },
                { n: 3, code: 'const initializeDatabase = async (config) => {' },
                { n: 4, code: '  if (!config.type) {' },
                { n: 5, code: '    throw new Error("Database type not selected");' },
                { n: 6, code: '  }' },
                { n: 7, code: '' },
                { n: 8, code: '  // TODO: Implement connection logic based on choice', cls: 'text-muted-foreground' },
                { n: 9, code: '  return await db.connect(config);' },
                { n: 10, code: '};' },
              ].map(({ n, code, cls }) => (
                <div key={n} className="flex gap-4">
                  <div className="text-muted-foreground/40 select-none text-right w-6">
                    {n}
                  </div>
                  <div className={cls ?? 'text-foreground/60'}>{code}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* ════════════════════════════════════════════════
          OVERLAY — ChoiceModal (both modes)
         ════════════════════════════════════════════════ */}
      <div
        className="absolute inset-0 z-50 flex items-center justify-center p-4 sm:p-6 lg:p-8
                   dark:bg-background/60 dark:backdrop-blur-sm
                   bg-muted"
      >
        <ChoiceModal
          projectId={params.projectId}
          apiOptions={choiceData?.options}
          title={choiceData?.context}
          onConfirm={handleSelect}
          onCancel={handleCancel}
          isSubmitting={selectChoice.isPending}
        />
      </div>
    </div>
  )
}
