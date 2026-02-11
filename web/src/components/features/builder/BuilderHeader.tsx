'use client'

import Link from 'next/link'
import {
  Code2,
  Play,
  Eye,
  Pencil,
  Rocket,
  Settings,
  Bell,
  Github,
} from 'lucide-react'
import { ThemeToggle } from '@/components/shared/ThemeToggle'
import { GitHubExportModal } from './GitHubExportModal'

interface BuilderHeaderProps {
  projectName: string
  projectId?: string
}

/**
 * BuilderHeader — Top nav bar for the Builder IDE.
 * Dark: terminal-style with editor/preview toggle + Run button
 * Light: VS-Code-style with breadcrumb + Run Build / Deploy
 */
export function BuilderHeader({ projectName, projectId }: BuilderHeaderProps) {
  return (
    <header className="h-14 shrink-0 z-20 flex items-center justify-between px-4 border-b border-border bg-background">
      {/* Left: Logo + mode label */}
      <div className="flex items-center gap-4">
        <Link href="/dashboard" className="flex items-center gap-2">
          <div className="size-8 flex items-center justify-center bg-cf-primary/20 dark:bg-cf-primary/20 rounded text-cf-primary">
            <Code2 className="size-5" />
          </div>
        </Link>
        {/* Dark-mode label */}
        <h1 className="hidden dark:flex items-center text-foreground font-bold text-lg tracking-tight">
          CodeForge
          <span className="text-muted-foreground font-normal text-sm ml-2">
            Builder Mode
          </span>
        </h1>
        {/* Light-mode label + menu */}
        <div className="flex dark:hidden items-center gap-2">
          <h2 className="text-foreground text-base font-bold tracking-tight">
            CodeForge
          </h2>
          <nav className="hidden md:flex items-center gap-6 ml-6">
            {['File', 'Edit', 'View', 'Go', 'Run', 'Terminal', 'Help'].map(
              (item) => (
                <button
                  key={item}
                  className="text-xs font-medium text-muted-foreground hover:text-foreground transition-colors"
                >
                  {item}
                </button>
              )
            )}
          </nav>
        </div>
      </div>

      {/* Center: Editor/Preview toggle (dark) | Breadcrumb widget (light) */}
      <div className="hidden dark:flex items-center">
        <div className="flex bg-secondary rounded-lg p-1 border border-border">
          <button className="flex items-center gap-2 px-3 py-1.5 bg-muted rounded text-xs font-medium text-foreground shadow-sm">
            <Pencil className="size-3.5" />
            Editor
          </button>
          <button className="flex items-center gap-2 px-3 py-1.5 hover:bg-muted/50 rounded text-xs font-medium text-muted-foreground transition-colors">
            <Eye className="size-3.5" />
            Preview
          </button>
        </div>
      </div>

      {/* Light-mode breadcrumb */}
      <div className="hidden lg:flex dark:hidden items-center gap-2 px-3 py-1.5 bg-muted rounded-lg border border-border">
        <Code2 className="size-4 text-muted-foreground" />
        <span className="text-xs font-semibold text-foreground">
          {projectName}
        </span>
        <span className="text-muted-foreground text-xs">/</span>
        <span className="text-xs text-muted-foreground">src</span>
        <span className="text-muted-foreground text-xs">/</span>
        <span className="text-xs text-muted-foreground">App.tsx</span>
      </div>

      {/* Right: Actions */}
      <div className="flex items-center gap-3">
        {/* Dark-mode Run */}
        <button className="hidden dark:flex items-center justify-center h-8 px-3 bg-cf-primary text-black text-sm font-bold rounded hover:brightness-110 transition-colors">
          <Play className="size-4 mr-1" />
          Run
        </button>

        {/* Light-mode buttons */}
        <button className="flex dark:hidden items-center justify-center h-8 px-3 bg-cf-primary/10 text-cf-primary hover:bg-cf-primary/20 rounded-lg transition-colors gap-2">
          <Play className="size-4" />
          <span className="text-xs font-bold">Run Build</span>
        </button>
        <button className="flex dark:hidden items-center justify-center h-8 px-3 bg-cf-primary text-white hover:brightness-110 rounded-lg transition-colors gap-2 shadow-sm">
          <Rocket className="size-4" />
          <span className="text-xs font-bold">Deploy</span>
        </button>

        {/* GitHub Export */}
        {projectId && (
          <GitHubExportModal
            projectId={projectId}
            projectName={projectName}
            trigger={
              <button className="flex items-center justify-center h-8 px-3 bg-muted hover:bg-muted/80 text-foreground rounded-lg transition-colors gap-2 border border-border">
                <Github className="size-4" />
                <span className="hidden sm:inline text-xs font-medium">Export</span>
              </button>
            }
          />
        )}

        <div className="h-6 w-px bg-border mx-1" />

        <ThemeToggle />

        <button
          className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted rounded-md"
          aria-label="Settings"
        >
          <Settings className="size-5" />
        </button>
        <button
          className="p-1.5 text-muted-foreground hover:text-foreground hover:bg-muted rounded-md"
          aria-label="Notifications"
        >
          <Bell className="size-5" />
        </button>

        {/* User avatar */}
        <div className="size-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 border border-border" />
      </div>
    </header>
  )
}
