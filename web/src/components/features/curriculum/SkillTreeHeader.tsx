'use client'

import Link from 'next/link'
import { Code2, User, Bell, Star, Award } from 'lucide-react'
import { ThemeToggle } from '@/components/shared/ThemeToggle'

/**
 * SkillTreeHeader — Top nav for the Skill Tree / Curriculum page.
 *
 * **Dark**: CodeForge logo, Path/Projects/Community nav, curriculum progress bar, rank badge, profile.
 * **Light**: CodeForge logo + path label, progress %, Level/XP badge, notifications, avatar.
 */
export function SkillTreeHeader() {
  return (
    <header className="h-16 shrink-0 z-50 border-b flex items-center justify-between px-6
                        dark:border-border/30 dark:bg-zinc-950/90 dark:backdrop-blur-sm
                        border-border bg-white shadow-sm">
      {/* ─── Left ─── */}
      <div className="flex items-center gap-4">
        <Link href="/dashboard" className="flex items-center gap-2">
          {/* Dark icon */}
          <div className="hidden dark:block size-8 text-cf-primary">
            <Code2 className="size-8" />
          </div>
          {/* Light icon */}
          <span className="block dark:hidden text-violet-600">
            <Code2 className="size-8" />
          </span>
          <h1 className="text-lg font-bold tracking-tight text-foreground hidden sm:block">
            CodeForge AI
          </h1>
        </Link>

        <div className="h-6 w-px bg-border mx-2 hidden sm:block" />

        {/* Dark nav */}
        <nav className="hidden dark:flex gap-1">
          {['Path', 'Projects', 'Community'].map((item, i) => (
            <Link
              key={item}
              href={i === 0 ? '/dashboard/curriculum' : '#'}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                i === 0
                  ? 'text-foreground hover:bg-muted/50'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted/50'
              }`}
            >
              {item}
            </Link>
          ))}
        </nav>

        {/* Light path + progress */}
        <div className="flex dark:hidden flex-col">
          <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Architect Path: Full Stack v2
          </span>
          <div className="flex items-center gap-2">
            <div className="w-32 h-2 bg-muted rounded-full overflow-hidden">
              <div className="h-full bg-foreground w-[45%] rounded-full" />
            </div>
            <span className="text-xs font-bold text-foreground">45%</span>
          </div>
        </div>
      </div>

      {/* ─── Right ─── */}
      <div className="flex items-center gap-6">
        {/* Dark progress + rank */}
        <div className="hidden dark:flex items-center gap-6">
          <div className="flex flex-col items-end gap-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-muted-foreground">CURRICULUM PROGRESS</span>
              <span className="text-xs font-mono text-cf-primary font-bold">45%</span>
            </div>
            <div className="w-32 h-1.5 bg-zinc-800 rounded-full overflow-hidden">
              <div className="h-full bg-cf-primary w-[45%] shadow-[0_0_10px_rgba(19,236,109,0.5)]" />
            </div>
          </div>
          <div className="flex items-center gap-2 bg-secondary border border-border px-3 py-1.5 rounded-lg">
            <Award className="size-4 text-cf-primary" />
            <span className="text-sm font-mono font-bold text-foreground">Junior Architect</span>
          </div>
        </div>

        {/* Light level badge */}
        <div className="flex dark:hidden items-center gap-2 px-3 py-1 bg-muted/50 rounded border border-border">
          <Star className="size-3.5 text-violet-600" />
          <span className="text-sm font-bold text-foreground">Level 4</span>
          <span className="text-xs text-muted-foreground font-medium">2400 XP</span>
        </div>

        <ThemeToggle />

        {/* Notifications (light) */}
        <button
          className="text-muted-foreground hover:text-foreground transition-colors block dark:hidden"
          aria-label="Notifications"
        >
          <Bell className="size-5" />
        </button>

        {/* Profile */}
        <button
          className="size-9 rounded-lg bg-muted flex items-center justify-center hover:bg-muted/80 transition-colors border border-border"
          aria-label="Profile"
        >
          <User className="size-4 text-muted-foreground" />
        </button>
      </div>
    </header>
  )
}
