'use client'

import { CheckCircle, Play, Rocket } from 'lucide-react'

/**
 * LabFooter — Bottom action bar for the Module Lab.
 *
 * **Dark**: Test-passing counter (0/3), Run Tests (violet outline),
 *           Submit Solution (emerald solid) buttons.
 * **Light**: System Ready status dot, Run Tests (outline),
 *            Submit Solution (primary solid) buttons.
 */
export function LabFooter() {
  return (
    <footer
      className="h-16 shrink-0 z-10 border-t flex items-center justify-between px-6
                 dark:border-zinc-800 dark:bg-zinc-950
                 border-border bg-white shadow-[0_-2px_10px_rgba(0,0,0,0.02)]"
    >
      {/* ── Left status ── */}
      <div className="flex items-center gap-2">
        {/* Dark */}
        <div className="hidden dark:flex items-center gap-2 text-muted-foreground">
          <CheckCircle className="size-[18px] text-emerald-500" />
          <span className="text-xs font-mono">Tests Passing: 0/3</span>
        </div>
        {/* Light */}
        <div className="flex dark:hidden items-center gap-2">
          <div className="size-2.5 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-sm font-medium text-muted-foreground">System Ready</span>
        </div>
      </div>

      {/* ── Right actions ── */}
      <div className="flex items-center gap-3 sm:gap-4">
        {/* Run Tests – dark */}
        <button className="hidden dark:flex h-9 px-4 rounded-sm border border-violet-500 text-violet-500 bg-transparent hover:bg-violet-500/10 transition-all text-sm font-bold items-center gap-2">
          <Play className="size-[18px]" />
          Run Tests
        </button>
        {/* Run Tests – light */}
        <button className="flex dark:hidden items-center gap-2 px-5 py-2.5 rounded border border-border bg-white text-foreground text-sm font-semibold hover:bg-muted/50 transition-colors shadow-sm">
          <Play className="size-[18px]" />
          Run Tests
        </button>

        {/* Submit – dark */}
        <button className="hidden dark:flex h-9 px-6 rounded-sm bg-emerald-500 hover:bg-emerald-400 text-white transition-all text-sm font-bold items-center gap-2 shadow-lg shadow-emerald-500/20">
          <Rocket className="size-[18px]" />
          Submit Solution
        </button>
        {/* Submit – light */}
        <button className="flex dark:hidden items-center gap-2 px-6 py-2.5 rounded bg-blue-600 text-white text-sm font-bold shadow-md shadow-blue-500/20 hover:bg-blue-700 transition-colors active:scale-[0.98]">
          <CheckCircle className="size-[18px]" />
          Submit Solution
        </button>
      </div>
    </footer>
  )
}
