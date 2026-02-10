'use client'

import { useState } from 'react'
import { Flag, Lightbulb, Check } from 'lucide-react'
import type { LearningModule } from '@/types/api.types'

/* ─── Dark objectives ─── */
const darkObjectives = [
  '01. Analyze query plan',
  '02. Create appropriate index',
  '03. Validate performance boost',
]

const darkCriteria = [
  { label: 'Identify slow query execution time', checked: true },
  { label: 'Write valid CREATE INDEX SQL statement', checked: false },
  { label: 'Reduce query cost by at least 50%', checked: false },
]

/* ─── Light tabs ─── */
const tabs = ['Instructions', 'Hints', 'Resources'] as const

export interface InstructionPanelProps {
  /** API module data for dynamic objectives; falls back to demo */
  module?: LearningModule
}

/**
 * InstructionPanel — Left sidebar in the Module Lab.
 *
 * Accepts optional module data from the API. Falls back to demo content.
 */
export function InstructionPanel({ module }: InstructionPanelProps) {
  const [activeTab, setActiveTab] = useState<(typeof tabs)[number]>('Instructions')
  const [criteria, setCriteria] = useState(darkCriteria)

  const toggleCriterion = (idx: number) =>
    setCriteria((prev) =>
      prev.map((c, i) => (i === idx ? { ...c, checked: !c.checked } : c)),
    )

  return (
    <>
      {/* ═══ DARK ═══ */}
      <aside className="hidden dark:flex w-[340px] shrink-0 border-r border-zinc-800 flex-col bg-zinc-950">
        {/* Header */}
        <div className="p-5 border-b border-zinc-800 flex items-center justify-between">
          <h3 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
            Instruction
          </h3>
          <span className="text-xs bg-zinc-800 text-zinc-300 px-2 py-0.5 rounded">Easy</span>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto custom-scrollbar p-5 space-y-6">
          {/* Title + description */}
          <div>
            <h1 className="text-2xl font-bold text-foreground mb-2">{module?.title ?? 'Database Indexing'}</h1>
            <p className="text-muted-foreground text-sm leading-relaxed">
              {module?.description ?? (<>Optimize query performance by implementing a B-Tree index on the{' '}
              <code className="bg-zinc-800 text-zinc-200 px-1 py-0.5 rounded text-xs font-mono">
                users
              </code>{' '}
              table. The current query scan is taking too long on the email column.</>)}
            </p>
          </div>

          {/* Objectives */}
          <div className="space-y-3">
            <h4 className="text-sm font-bold text-foreground flex items-center gap-2">
              <Flag className="size-[18px] text-violet-500" />
              Objectives
            </h4>
            <div className="bg-zinc-900/50 rounded border border-zinc-800 p-4 font-mono text-xs text-zinc-300 space-y-2">
              {(module?.objectives ?? darkObjectives).map((obj, i) => {
                const text = typeof obj === 'string' ? obj : String(obj)
                const [num, ...rest] = text.split(' ')
                return (
                  <p key={text} className="flex items-start gap-2">
                    <span className="text-zinc-600">{module ? `${String(i + 1).padStart(2, '0')}.` : num}</span> {module ? text : rest.join(' ')}
                  </p>
                )
              })}
            </div>
          </div>

          {/* Success criteria */}
          <div className="space-y-3">
            <h4 className="text-sm font-bold text-foreground">Success Criteria</h4>
            <div className="space-y-2">
              {criteria.map((c, i) => (
                <label
                  key={c.label}
                  className="flex items-start gap-3 p-3 rounded hover:bg-zinc-900/50 transition-colors border border-transparent hover:border-zinc-800 cursor-pointer group"
                >
                  <div className="relative flex items-center justify-center size-5 mt-0.5">
                    <input
                      type="checkbox"
                      checked={c.checked}
                      onChange={() => toggleCriterion(i)}
                      className="peer size-5 appearance-none rounded border-2 border-zinc-600 bg-transparent checked:border-violet-500 checked:bg-violet-500/20 transition-all cursor-pointer"
                    />
                    <Check
                      className="absolute size-4 text-violet-500 opacity-0 peer-checked:opacity-100 pointer-events-none"
                      strokeWidth={3}
                    />
                  </div>
                  <span
                    className={`text-sm transition-colors ${
                      c.checked
                        ? 'text-zinc-300 line-through decoration-zinc-600'
                        : 'text-muted-foreground group-hover:text-zinc-200'
                    }`}
                  >
                    {c.label}
                  </span>
                </label>
              ))}
            </div>
          </div>
        </div>
      </aside>

      {/* ═══ LIGHT ═══ */}
      <section className="flex dark:hidden w-[350px] min-w-[300px] max-w-[500px] flex-col border-r border-border bg-muted/30">
        {/* Task header */}
        <div className="p-6 border-b border-border bg-white">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
              Task 1.2
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-700 border border-emerald-200">
              EASY
            </span>
          </div>
          <h2 className="text-xl font-bold text-foreground leading-tight mb-2">
            Fibonacci Sequence
          </h2>
          {/* Tabs */}
          <div className="flex gap-4 border-b border-muted pb-px">
            {tabs.map((t) => (
              <button
                key={t}
                onClick={() => setActiveTab(t)}
                className={`pb-2 text-sm font-medium border-b-2 transition-all ${
                  activeTab === t
                    ? 'text-blue-600 border-blue-600 font-semibold'
                    : 'text-muted-foreground hover:text-foreground border-transparent hover:border-muted-foreground/30'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          <div>
            <p className="text-sm text-muted-foreground leading-relaxed mb-4">
              Your task is to implement a function that returns the{' '}
              <code className="bg-muted px-1 rounded text-foreground text-xs font-mono">n</code>-th
              number in the Fibonacci sequence.
            </p>
            <p className="text-sm text-muted-foreground leading-relaxed">
              The sequence starts with 0 and 1. Each subsequent number is the sum of the previous
              two.
            </p>
          </div>

          {/* Math definition card */}
          <div className="bg-white border border-border rounded p-4">
            <h3 className="text-xs font-bold text-foreground uppercase tracking-wide mb-2">
              Mathematical Definition
            </h3>
            <div className="font-mono text-xs text-muted-foreground bg-muted/50 p-2 rounded">
              F(0) = 0<br />
              F(1) = 1<br />
              F(n) = F(n-1) + F(n-2) for n &gt; 1
            </div>
          </div>

          {/* Example I/O */}
          <div>
            <h3 className="text-sm font-bold text-foreground mb-2">Example Input / Output</h3>
            <div className="space-y-2">
              {[
                { label: 'Input:', value: 'n = 3' },
                { label: 'Output:', value: '2' },
              ].map((row) => (
                <div key={row.label} className="flex items-start gap-3 text-sm">
                  <span className="font-mono text-muted-foreground min-w-[60px]">{row.label}</span>
                  <span className="font-mono text-foreground">{row.value}</span>
                </div>
              ))}
              <div className="flex items-start gap-3 text-sm">
                <span className="font-mono text-muted-foreground min-w-[60px]">Explanation:</span>
                <span className="text-muted-foreground">
                  The sequence is 0, 1, 1, 2. The 3rd index is 2.
                </span>
              </div>
            </div>
          </div>

          {/* Tip */}
          <div className="bg-amber-50 border border-amber-200 rounded p-4 flex gap-3">
            <Lightbulb className="size-4 text-amber-600 mt-0.5 shrink-0" />
            <div className="text-xs text-amber-800">
              <span className="font-bold">Tip:</span> Consider handling the base cases where n is 0
              or 1 explicitly at the beginning of your function.
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
