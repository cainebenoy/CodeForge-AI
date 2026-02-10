'use client'

import { useState } from 'react'
import {
  Brain,
  Check,
  ChevronUp,
  ChevronDown,
  Clock,
  Coins,
  Terminal,
} from 'lucide-react'

/* ─── Types ─── */
export type StepStatus = 'completed' | 'active' | 'pending'

export interface ReasoningStep {
  id: string
  label: string
  /** Short description (light mode) */
  description?: string
  status: StepStatus
  /** e.g. "00:01.24" (dark) or "120ms" (light) */
  time?: string
  /** Sub-lines shown under the active step in dark mode */
  subLines?: string[]
  /** Extra info badges (light mode) e.g. ["Found: 14 files", "Context: TypeScript"] */
  badges?: string[]
  /** Expandable detail shown on hover (dark mode) */
  hoverDetail?: string
}

export interface TerminalLogLine {
  time: string
  text: string
  bold?: boolean
}

/* ─── Demo data ─── */
const defaultDarkSteps: ReasoningStep[] = [
  {
    id: '1',
    label: 'Researching requirements',
    status: 'completed',
    time: '00:01.24',
    hoverDetail: 'Found 12 matching patterns in knowledge base.',
  },
  {
    id: '2',
    label: 'Checking API compatibility',
    status: 'completed',
    time: '00:03.50',
  },
  {
    id: '3',
    label: 'Generating schema',
    status: 'active',
    time: '00:04.12',
    subLines: [
      'Defining User table structure...',
      'Setting up foreign keys for Orders...',
      'Optimizing indexes...',
    ],
  },
  { id: '4', label: 'Validating output', status: 'pending' },
  { id: '5', label: 'Writing migration files', status: 'pending' },
]

const defaultLightSteps: ReasoningStep[] = [
  {
    id: '1',
    label: 'Parse user requirements',
    description: 'Analyzed natural language prompt for technical specs.',
    status: 'completed',
    time: '120ms',
  },
  {
    id: '2',
    label: 'Scan project structure',
    status: 'completed',
    badges: ['Found: 14 files', 'Context: TypeScript'],
  },
  {
    id: '3',
    label: 'Generate API boilerplate',
    status: 'active',
  },
  { id: '4', label: 'Refactor database schema', status: 'pending' },
  { id: '5', label: 'Run unit tests', status: 'pending' },
]

const defaultLogLines: TerminalLogLine[] = [
  { time: '15:04:22', text: 'writing /src/routes/auth.ts' },
  { time: '15:04:23', text: 'importing express, jwt, bcrypt...' },
  { time: '15:04:23', text: 'defining router endpoints...' },
  { time: '15:04:24', text: 'validating imports', bold: true },
]

/* ─── Helpers ─── */
function statusPrefix(s: StepStatus) {
  return s === 'completed' ? '[Done]' : s === 'active' ? '[Active]' : '[Pending]'
}

/* ═══════════════════════════════════════════
   DARK-MODE: Terminal-style log accordion
   ═══════════════════════════════════════════ */
function DarkAccordion({
  steps,
  open,
  toggle,
}: {
  steps: ReasoningStep[]
  open: boolean
  toggle: () => void
}) {
  return (
    <div className="rounded-xl overflow-hidden border border-border/30 shadow-2xl bg-zinc-900">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 bg-zinc-900 border-b border-border/30">
        <div className="flex items-center gap-3">
          <Brain className="size-5 text-amber-400" />
          <span className="text-zinc-200 text-sm font-semibold tracking-wide uppercase">
            Agent Reasoning
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-xs font-mono text-amber-400 bg-amber-400/10 px-2 py-1 rounded">
            Thinking...
          </span>
          <button
            onClick={toggle}
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label={open ? 'Collapse' : 'Expand'}
          >
            {open ? (
              <ChevronUp className="size-5" />
            ) : (
              <ChevronDown className="size-5" />
            )}
          </button>
        </div>
      </div>

      {/* Collapsible body */}
      {open && (
        <>
          {/* Terminal log */}
          <div className="p-6 bg-zinc-900 font-mono text-sm leading-relaxed">
            <div className="flex flex-col gap-3">
              {steps.map((step) => {
                if (step.status === 'completed') {
                  return (
                    <div key={step.id} className="flex gap-4 group">
                      <span className="text-zinc-600 w-[80px] shrink-0 text-right select-none opacity-50">
                        {step.time}
                      </span>
                      <div className="flex flex-col">
                        <span className="text-zinc-500 line-through decoration-zinc-700/50 decoration-1">
                          {statusPrefix(step.status)} {step.label}
                        </span>
                        {step.hoverDetail && (
                          <span className="text-zinc-700 text-xs pl-4 pt-1 hidden group-hover:block transition-all">
                            {step.hoverDetail}
                          </span>
                        )}
                      </div>
                    </div>
                  )
                }

                if (step.status === 'active') {
                  return (
                    <div key={step.id} className="flex gap-4">
                      <span className="text-amber-400 w-[80px] shrink-0 text-right select-none font-bold">
                        {step.time}
                      </span>
                      <div className="flex flex-col">
                        <span className="text-amber-400 font-medium animate-pulse">
                          {statusPrefix(step.status)} {step.label}
                          <span className="inline-block w-[2px] h-4 bg-amber-400 ml-0.5 align-middle animate-pulse" />
                        </span>
                        {step.subLines && (
                          <div className="pl-4 pt-2 text-amber-400/70 text-xs space-y-0.5">
                            {step.subLines.map((l, i) => (
                              <div key={i}>&gt; {l}</div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  )
                }

                /* pending */
                return (
                  <div key={step.id} className="flex gap-4 opacity-40">
                    <span className="text-zinc-700 w-[80px] shrink-0 text-right select-none">
                      --:--.--
                    </span>
                    <span className="text-zinc-600">
                      {statusPrefix(step.status)} {step.label}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Meta footer */}
          <div className="px-6 py-2 bg-black/20 border-t border-border/30 flex justify-between items-center text-xs font-mono text-zinc-600">
            <span>Agent_ID: v4.2.0-alpha</span>
            <span>Thread: #8f92a1</span>
          </div>
        </>
      )}
    </div>
  )
}

/* ═══════════════════════════════════════════
   LIGHT-MODE: Stepper-timeline accordion
   ═══════════════════════════════════════════ */
function LightAccordion({
  steps,
  logLines,
  open,
  toggle,
}: {
  steps: ReasoningStep[]
  logLines: TerminalLogLine[]
  open: boolean
  toggle: () => void
}) {
  return (
    <div className="rounded-xl overflow-hidden shadow-sm border border-border bg-white">
      {/* Header */}
      <button
        onClick={toggle}
        className="w-full flex items-center justify-between p-4 bg-muted/30 hover:bg-muted/50 transition-colors select-none cursor-pointer"
      >
        <div className="flex items-center gap-3">
          {/* Pulsing status dot */}
          <div className="relative flex h-3 w-3">
            <span className="absolute inline-flex h-full w-full rounded-full bg-cf-primary opacity-75 animate-ping" />
            <span className="relative inline-flex rounded-full h-3 w-3 bg-cf-primary" />
          </div>
          <div className="flex flex-col items-start">
            <span className="text-sm font-semibold text-foreground tracking-tight flex items-center gap-2">
              Agent Reasoning
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-cf-primary/20 text-emerald-800">
                THINKING
              </span>
            </span>
            <span className="text-xs text-muted-foreground font-mono">
              ID: req_8f92a1 • Model: Claude 3.5 Sonnet
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 text-xs text-muted-foreground font-mono">
            <span className="flex items-center gap-1">
              <Clock className="size-3.5" /> 3.4s
            </span>
            <span className="h-3 w-px bg-border" />
            <span className="flex items-center gap-1">
              <Coins className="size-3.5" /> 450
            </span>
          </div>
          <ChevronDown
            className={`size-5 text-muted-foreground transition-transform duration-200 ${open ? 'rotate-180' : ''}`}
          />
        </div>
      </button>

      {open && (
        <div className="border-t border-border bg-muted/20">
          {/* Progress bar */}
          <div className="h-1 w-full bg-muted">
            <div
              className="h-full bg-cf-primary shadow-[0_0_10px_rgba(19,236,109,0.5)] transition-all duration-500 ease-out"
              style={{ width: '60%' }}
            />
          </div>

          {/* Steps */}
          <div className="p-6 space-y-1">
            {steps.map((step, idx) => {
              const isLast = idx === steps.length - 1

              /* ── Completed ── */
              if (step.status === 'completed') {
                return (
                  <div
                    key={step.id}
                    className={`relative pl-8 pb-6 ${isLast ? '' : 'border-l border-border'}`}
                  >
                    <div className="absolute -left-[9px] top-0 h-5 w-5 rounded-full bg-cf-primary flex items-center justify-center ring-4 ring-background">
                      <Check className="size-3 text-white" strokeWidth={3} />
                    </div>
                    <div className="flex justify-between items-start -mt-0.5">
                      <div className="flex flex-col gap-1">
                        <h3 className="text-sm font-medium text-foreground">
                          {step.label}
                        </h3>
                        {step.description && (
                          <p className="text-xs text-muted-foreground">
                            {step.description}
                          </p>
                        )}
                        {step.badges && step.badges.length > 0 && (
                          <div className="flex gap-2 mt-1">
                            {step.badges.map((b) => (
                              <span
                                key={b}
                                className="text-[10px] font-mono border border-border bg-background text-muted-foreground px-1.5 py-0.5 rounded"
                              >
                                {b}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                      {step.time && (
                        <span className="text-xs font-mono text-muted-foreground bg-muted px-1.5 py-0.5 rounded">
                          {step.time}
                        </span>
                      )}
                    </div>
                  </div>
                )
              }

              /* ── Active ── */
              if (step.status === 'active') {
                return (
                  <div
                    key={step.id}
                    className={`relative pl-8 pb-8 ${isLast ? '' : 'border-l border-border'}`}
                  >
                    {/* Pulsing ring node */}
                    <div className="absolute -left-[9px] top-0 h-5 w-5 rounded-full bg-background border-2 border-cf-primary flex items-center justify-center ring-4 ring-background shadow-[0_0_8px_rgba(19,236,109,0.4)]">
                      <div className="h-1.5 w-1.5 rounded-full bg-cf-primary animate-pulse" />
                    </div>
                    <div className="flex flex-col gap-3 -mt-0.5">
                      <div className="flex justify-between items-center">
                        <h3 className="text-sm font-bold text-foreground flex items-center gap-2">
                          {step.label}
                          <span className="relative flex h-1.5 w-1.5">
                            <span className="absolute inline-flex h-full w-full rounded-full bg-cf-primary opacity-75 animate-ping" />
                            <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-cf-primary" />
                          </span>
                        </h3>
                      </div>

                      {/* Mini terminal */}
                      <div className="w-full bg-zinc-900 rounded-lg p-3 font-mono text-xs overflow-hidden border border-zinc-800 shadow-inner">
                        {/* Traffic lights */}
                        <div className="flex items-center gap-1.5 mb-2 border-b border-zinc-800 pb-2">
                          <div className="w-2 h-2 rounded-full bg-red-500/50" />
                          <div className="w-2 h-2 rounded-full bg-yellow-500/50" />
                          <div className="w-2 h-2 rounded-full bg-green-500/50" />
                          <span className="ml-2 text-zinc-500">
                            agent-process — zsh
                          </span>
                        </div>
                        <div className="flex flex-col gap-1 custom-scrollbar max-h-32 overflow-y-auto">
                          {logLines.map((line, i) => (
                            <div
                              key={i}
                              className={`flex gap-2 ${line.bold ? 'animate-pulse' : ''}`}
                            >
                              <span className="text-zinc-500 select-none">
                                {line.time}
                              </span>
                              <span className="text-cf-primary">&gt;&gt;</span>
                              <span
                                className={
                                  line.bold
                                    ? 'text-zinc-100 font-bold'
                                    : 'text-zinc-300'
                                }
                              >
                                {line.text}
                                {line.bold && (
                                  <span className="inline-block w-[2px] h-3 bg-zinc-100 ml-0.5 align-middle animate-pulse" />
                                )}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )
              }

              /* ── Pending ── */
              return (
                <div
                  key={step.id}
                  className={`relative pl-8 pb-6 ${isLast ? 'border-l border-transparent' : 'border-l border-border'} opacity-50`}
                >
                  <div className="absolute -left-[5px] top-1 h-2.5 w-2.5 rounded-full bg-muted-foreground/30 ring-4 ring-background" />
                  <h3 className="text-sm font-medium text-muted-foreground">
                    {step.label}
                  </h3>
                </div>
              )
            })}
          </div>

          {/* Footer */}
          <div className="border-t border-border p-3 bg-muted/30 flex justify-between items-center rounded-b-xl">
            <span className="text-xs text-muted-foreground font-mono pl-2">
              Last updated: Just now
            </span>
            <div className="flex gap-2">
              <button className="px-3 py-1.5 text-xs font-medium text-muted-foreground hover:text-foreground hover:bg-muted rounded transition-colors">
                Cancel
              </button>
              <button className="px-3 py-1.5 text-xs font-medium text-foreground bg-background border border-border hover:border-cf-primary rounded shadow-sm transition-all flex items-center gap-1.5 group">
                <Terminal className="size-3.5 group-hover:text-cf-primary transition-colors" />
                View Full Logs
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

/* ═══════════════════════════════════════════
   PUBLIC: AgentReasoningAccordion
   ═══════════════════════════════════════════ */

export interface AgentReasoningAccordionProps {
  darkSteps?: ReasoningStep[]
  lightSteps?: ReasoningStep[]
  logLines?: TerminalLogLine[]
  defaultOpen?: boolean
}

/**
 * AgentReasoningAccordion — Live agent reasoning display.
 *
 * **Dark**: Terminal-style timestamped log with [Done]/[Active]/[Pending] prefixes,
 *           amber accent, hover-reveal details on completed steps.
 * **Light**: Vertical stepper timeline with checkmarks, embedded mini-terminal
 *            on the active step, progress bar, and action footer.
 */
export function AgentReasoningAccordion({
  darkSteps = defaultDarkSteps,
  lightSteps = defaultLightSteps,
  logLines = defaultLogLines,
  defaultOpen = true,
}: AgentReasoningAccordionProps) {
  const [open, setOpen] = useState(defaultOpen)
  const toggle = () => setOpen((v) => !v)

  return (
    <>
      {/* Dark mode */}
      <div className="hidden dark:block">
        <DarkAccordion steps={darkSteps} open={open} toggle={toggle} />
      </div>
      {/* Light mode */}
      <div className="block dark:hidden">
        <LightAccordion
          steps={lightSteps}
          logLines={logLines}
          open={open}
          toggle={toggle}
        />
      </div>
    </>
  )
}
