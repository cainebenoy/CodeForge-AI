'use client'

import Link from 'next/link'
import { Code2, Bell, HelpCircle, User, Clock } from 'lucide-react'
import { ThemeToggle } from '@/components/shared/ThemeToggle'
import { useUser } from '@/lib/hooks/use-user'

export interface LabHeaderProps {
  /** Project title for breadcrumb */
  projectTitle?: string
  /** Current module title */
  moduleTitle?: string
  /** Module progress percentage (0-100) */
  moduleProgress?: number
}

/**
 * LabHeader — Top navigation for the Module Lab page.
 *
 * Accepts optional dynamic props from the lab page. Falls back to demo content.
 */
export function LabHeader({
  projectTitle,
  moduleTitle,
  moduleProgress,
}: LabHeaderProps) {
  const { user } = useUser()
  const initials = user?.user_metadata?.full_name
    ? user.user_metadata.full_name.split(' ').map((n: string) => n[0]).join('').toUpperCase().slice(0, 2)
    : user?.email?.slice(0, 2).toUpperCase() ?? 'JD'
  const avatarUrl = user?.user_metadata?.avatar_url
  return (
    <header
      className="h-14 shrink-0 z-10 border-b flex items-center justify-between px-4 sm:px-6
                 dark:border-zinc-800 dark:bg-zinc-950
                 border-border bg-white"
    >
      {/* ── Left ── */}
      <div className="flex items-center gap-4 sm:gap-6">
        {/* Logo */}
        <Link href="/dashboard" className="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <Code2 className="size-7 dark:text-violet-500 text-blue-600" />
          <h2 className="text-lg font-bold tracking-tight text-foreground hidden sm:block">
            CodeForge AI
          </h2>
        </Link>

        {/* Separator */}
        <div className="h-4 w-px dark:bg-zinc-700 bg-gray-300" />

        {/* Dark breadcrumbs */}
        <nav className="hidden dark:flex items-center gap-2 text-sm">
          <Link href="#" className="text-muted-foreground hover:text-foreground transition-colors">
            Student Mode
          </Link>
          <span className="text-zinc-600">/</span>
          <Link href="#" className="text-muted-foreground hover:text-foreground transition-colors">
            Modules
          </Link>
          <span className="text-zinc-600">/</span>
          <span className="text-violet-500 font-medium">{moduleTitle ?? 'Database Indexing'}</span>
        </nav>

        {/* Light module + progress */}
        <div className="flex dark:hidden flex-col justify-center">
          <h1 className="text-sm font-semibold text-foreground leading-tight">
            {moduleTitle ?? 'Module 1: Intro to Python'}
          </h1>
          <div className="flex items-center gap-2">
            <div className="h-1.5 w-24 bg-muted rounded-full overflow-hidden">
              <div className="h-full bg-blue-600 rounded-full" style={{ width: `${moduleProgress ?? 35}%` }} />
            </div>
            <span className="text-[10px] text-muted-foreground font-medium">{Math.round(moduleProgress ?? 35)}% Complete</span>
          </div>
        </div>
      </div>

      {/* ── Right ── */}
      <div className="flex items-center gap-3 sm:gap-4">
        {/* Timer (light only) */}
        <div className="hidden dark:hidden sm:flex items-center gap-1 text-muted-foreground bg-muted/50 px-3 py-1.5 rounded border border-border">
          <Clock className="size-[18px]" />
          <span className="text-xs font-mono font-medium">00:42:15</span>
        </div>

        <ThemeToggle />

        {/* Notifications (dark) */}
        <button
          className="hidden dark:flex size-8 rounded items-center justify-center text-muted-foreground hover:text-foreground hover:bg-zinc-800 transition-colors"
          aria-label="Notifications"
        >
          <Bell className="size-5" />
        </button>

        {/* Help */}
        <button
          className="flex items-center gap-1.5 text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Help"
        >
          <HelpCircle className="size-5" />
          <span className="text-sm font-medium hidden dark:hidden sm:inline">Help</span>
        </button>

        {/* Avatar */}
        <div className="dark:border-zinc-700 border-border border rounded-full">
          {avatarUrl ? (
            <img
              src={avatarUrl}
              alt="User avatar"
              className="size-8 rounded-full object-cover"
            />
          ) : (
            <div className="size-8 rounded-full bg-muted flex items-center justify-center text-xs font-bold dark:text-violet-500 text-muted-foreground">
              {initials}
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
