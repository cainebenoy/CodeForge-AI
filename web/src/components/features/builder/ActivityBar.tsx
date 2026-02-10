'use client'

import {
  FolderOpen,
  Search,
  GitBranch,
  Bug,
  Puzzle,
  User,
  Settings,
} from 'lucide-react'

/**
 * ActivityBar — VS-Code-style icon strip on the far left (light mode only, hidden in dark mode).
 */
export function ActivityBar() {
  const topIcons = [
    { icon: FolderOpen, label: 'Explorer', active: true },
    { icon: Search, label: 'Search' },
    { icon: GitBranch, label: 'Source Control', badge: true },
    { icon: Bug, label: 'Debug' },
    { icon: Puzzle, label: 'Extensions' },
  ]

  const bottomIcons = [
    { icon: User, label: 'Account' },
    { icon: Settings, label: 'Settings' },
  ]

  return (
    <aside className="w-12 shrink-0 border-r border-border bg-background flex flex-col items-center py-4 gap-4 z-10 dark:hidden">
      {topIcons.map(({ icon: Icon, label, active, badge }) => (
        <button
          key={label}
          className={`relative p-2 rounded transition-colors ${
            active
              ? 'text-cf-primary'
              : 'text-muted-foreground hover:text-foreground hover:bg-muted'
          }`}
          aria-label={label}
        >
          {active && (
            <div className="absolute left-0 top-2 bottom-2 w-0.5 bg-cf-primary rounded-r" />
          )}
          <Icon className="size-6" />
          {badge && (
            <span className="absolute top-1 right-1 size-2 bg-blue-500 rounded-full border border-background" />
          )}
        </button>
      ))}

      <div className="mt-auto flex flex-col gap-4">
        {bottomIcons.map(({ icon: Icon, label }) => (
          <button
            key={label}
            className="text-muted-foreground hover:text-foreground p-2 rounded hover:bg-muted transition-colors"
            aria-label={label}
          >
            <Icon className="size-6" />
          </button>
        ))}
      </div>
    </aside>
  )
}
