'use client'

import { useMemo, useCallback } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Code2, Loader2 } from 'lucide-react'
import { ThemeToggle } from '@/components/shared/ThemeToggle'
import {
  AgentReasoningAccordion,
  ProgressSummaryCards,
} from '@/components/features/reasoning'
import type { ReasoningStep, TerminalLogLine, SummaryCardData } from '@/components/features/reasoning'
import { useProjectJobs, useJobStatus } from '@/lib/hooks/use-agents'
import { useProject } from '@/lib/hooks/use-project'
import { useProjectRealtime } from '@/lib/hooks/use-realtime'
import { Database, Globe, Shield } from 'lucide-react'
import type { JobStatus } from '@/types/api.types'

/**
 * Maps a backend JobStatus to the UI ReasoningStep format.
 */
function jobsToSteps(jobs: JobStatus[]): ReasoningStep[] {
  return jobs.map((job) => {
    const status: ReasoningStep['status'] =
      job.status === 'completed' ? 'completed'
      : job.status === 'running' ? 'active'
      : job.status === 'failed' ? 'completed'
      : 'pending'

    const elapsed = job.completed_at && job.created_at
      ? `${((new Date(job.completed_at).getTime() - new Date(job.created_at).getTime()) / 1000).toFixed(2)}s`
      : job.status === 'running' ? `${job.progress}%`
      : undefined

    return {
      id: job.job_id,
      label: `${job.agent_type.charAt(0).toUpperCase() + job.agent_type.slice(1)} Agent`,
      description: job.error ?? undefined,
      status,
      time: elapsed,
      subLines: job.status === 'running'
        ? [`Processing... (${job.progress}% complete)`]
        : undefined,
    }
  })
}

function jobsToSummaryCards(jobs: JobStatus[]): SummaryCardData[] {
  const agentIcons: Record<string, React.ReactNode> = {
    research: <Globe className="size-5" />,
    wireframe: <Database className="size-5" />,
    code: <Shield className="size-5" />,
    qa: <Shield className="size-5" />,
  }

  return jobs
    .filter((j) => j.status === 'completed' && j.result)
    .slice(0, 3)
    .map((job) => ({
      icon: agentIcons[job.agent_type] ?? <Globe className="size-5" />,
      title: `${job.agent_type.charAt(0).toUpperCase() + job.agent_type.slice(1)}`,
      description: job.result
        ? typeof job.result === 'object' && 'summary' in (job.result as Record<string, unknown>)
          ? String((job.result as Record<string, unknown>).summary).slice(0, 80)
          : 'Completed successfully.'
        : 'Pending.',
    }))
}

/**
 * Project Generation Status page.
 *
 * Fetches live job data for the project and maps it to the agent reasoning UI.
 * Falls back to demo data when API is unavailable.
 */
export default function ProjectStatusPage({
  params,
}: {
  params: { projectId: string }
}) {
  const { data: project } = useProject(params.projectId)
  const { data: jobsData, isLoading } = useProjectJobs(params.projectId)

  // Real-time: auto-refresh when agent jobs or project change
  useProjectRealtime(params.projectId)

  const jobs = jobsData?.items ?? []

  const darkSteps = useMemo(() => (jobs.length > 0 ? jobsToSteps(jobs) : undefined), [jobs])
  const lightSteps = useMemo(() => (jobs.length > 0 ? jobsToSteps(jobs) : undefined), [jobs])
  const summaryCards = useMemo(() => (jobs.length > 0 ? jobsToSummaryCards(jobs) : undefined), [jobs])

  const isProcessing = jobs.some((j) => j.status === 'running' || j.status === 'queued')

  return (
    <>
      {/* ══════════════════════════════════
          DARK MODE — full page layout
         ══════════════════════════════════ */}
      <div className="hidden dark:flex flex-col min-h-screen bg-background text-foreground">
        {/* Header */}
        <header className="flex items-center justify-between px-6 py-4 border-b border-border mb-4 max-w-[960px] w-full mx-auto">
          <Link href="/dashboard" className="flex items-center gap-4">
            <div className="size-8 flex items-center justify-center bg-amber-400/20 rounded-lg text-amber-400">
              <Code2 className="size-5" />
            </div>
            <h2 className="text-foreground text-xl font-bold tracking-tight">
              CodeForge AI
            </h2>
          </Link>
          <div className="flex items-center gap-8">
            <nav className="hidden md:flex items-center gap-9">
              <Link
                href="/dashboard"
                className="text-muted-foreground hover:text-foreground text-sm font-medium transition-colors"
              >
                Dashboard
              </Link>
              <span className="text-foreground text-sm font-medium border-b border-amber-400 pb-0.5">
                Projects
              </span>
              <Link
                href="#"
                className="text-muted-foreground hover:text-foreground text-sm font-medium transition-colors"
              >
                Settings
              </Link>
            </nav>
            <ThemeToggle />
            <div className="size-10 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 border-2 border-amber-400/20" />
          </div>
        </header>

        {/* Body */}
        <div className="px-4 md:px-12 lg:px-40 flex flex-1 justify-center py-5">
          <div className="flex flex-col max-w-[960px] flex-1 gap-8">
            {/* Title area */}
            <div className="flex flex-col gap-2 px-4">
              <div className="flex items-center gap-3">
                <h1 className="text-foreground tracking-tight text-[32px] font-bold leading-tight">
                  {project?.title ? `${project.title} — Status` : 'Project Generation Status'}
                </h1>
                {isProcessing && (
                  <span className="flex h-2 w-2 rounded-full bg-amber-400 animate-pulse shadow-[0_0_8px_rgba(236,164,19,0.6)]" />
                )}
              </div>
              <p className="text-muted-foreground text-sm max-w-2xl">
                Real-time monitoring of the autonomous agent as it constructs
                your backend architecture.
              </p>
            </div>

            {/* Reasoning accordion + summary cards */}
            <div className="flex flex-col px-4 gap-6">
              {isLoading ? (
                <div className="flex items-center justify-center py-20">
                  <Loader2 className="size-8 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <>
                  <AgentReasoningAccordion
                    darkSteps={darkSteps}
                    lightSteps={lightSteps}
                  />
                  <ProgressSummaryCards cards={summaryCards} />
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ══════════════════════════════════
          LIGHT MODE — centred accordion
         ══════════════════════════════════ */}
      <div className="flex dark:hidden items-center justify-center min-h-screen bg-background p-4 sm:p-6 lg:p-8">
        <div className="w-full max-w-3xl">
          {isLoading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="size-8 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <AgentReasoningAccordion
              lightSteps={lightSteps}
              darkSteps={darkSteps}
            />
          )}
        </div>
      </div>
    </>
  )
}
