import Link from 'next/link'
import { Code2 } from 'lucide-react'
import { ThemeToggle } from '@/components/shared/ThemeToggle'
import {
  AgentReasoningAccordion,
  ProgressSummaryCards,
} from '@/components/features/reasoning'

/**
 * Project Generation Status page.
 *
 * **Dark**: Full page with header, title area ("Project Generation Status"),
 *           Agent Reasoning accordion (terminal-style), and progress summary cards.
 * **Light**: Centred standalone Agent Reasoning accordion (stepper-style).
 *
 * Route: /dashboard/project/[projectId]
 */
export default function ProjectStatusPage({
  params,
}: {
  params: { projectId: string }
}) {
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
                  Project Generation Status
                </h1>
                <span className="flex h-2 w-2 rounded-full bg-amber-400 animate-pulse shadow-[0_0_8px_rgba(236,164,19,0.6)]" />
              </div>
              <p className="text-muted-foreground text-sm max-w-2xl">
                Real-time monitoring of the autonomous agent as it constructs
                your backend architecture.
              </p>
            </div>

            {/* Reasoning accordion + summary cards */}
            <div className="flex flex-col px-4 gap-6">
              <AgentReasoningAccordion />
              <ProgressSummaryCards />
            </div>
          </div>
        </div>
      </div>

      {/* ══════════════════════════════════
          LIGHT MODE — centred accordion
         ══════════════════════════════════ */}
      <div className="flex dark:hidden items-center justify-center min-h-screen bg-background p-4 sm:p-6 lg:p-8">
        <div className="w-full max-w-3xl">
          <AgentReasoningAccordion />
        </div>
      </div>
    </>
  )
}
