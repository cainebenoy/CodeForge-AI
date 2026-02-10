'use client'

import { X, FileCode, FileText } from 'lucide-react'

export interface EditorTab {
  name: string
  icon: 'tsx' | 'css' | 'json' | 'ts'
  active?: boolean
}

const defaultTabs: EditorTab[] = [
  { name: 'App.tsx', icon: 'tsx', active: true },
  { name: 'index.css', icon: 'css' },
  { name: 'package.json', icon: 'json' },
]

const iconColorMap: Record<string, string> = {
  tsx: 'text-blue-400',
  css: 'text-yellow-400',
  json: 'text-orange-400',
  ts: 'text-purple-400',
}

function TabIcon({ icon }: { icon: string }) {
  const color = iconColorMap[icon] ?? 'text-muted-foreground'
  return icon === 'css' ? (
    <FileText className={`size-3.5 ${color}`} />
  ) : (
    <FileCode className={`size-3.5 ${color}`} />
  )
}

/**
 * EditorTabs — Tab bar above the code editor.
 * Active tab has a top accent border; idle tabs show close button on hover.
 */
export function EditorTabs({ tabs = defaultTabs }: { tabs?: EditorTab[] }) {
  return (
    <div className="flex items-center bg-muted/50 dark:bg-background border-b border-border overflow-x-auto">
      {tabs.map((tab) => (
        <div
          key={tab.name}
          className={`flex items-center gap-2 px-4 py-2 text-sm min-w-[140px] justify-between group cursor-pointer transition-colors ${
            tab.active
              ? 'bg-background dark:bg-black border-t-2 border-t-cf-primary text-foreground font-medium'
              : 'border-r border-border/50 text-muted-foreground hover:bg-muted/80 dark:hover:bg-muted/50'
          }`}
        >
          <div className="flex items-center gap-2">
            <TabIcon icon={tab.icon} />
            <span className="truncate">{tab.name}</span>
          </div>
          <button
            className="opacity-0 group-hover:opacity-100 hover:bg-muted rounded p-0.5 transition-all"
            aria-label={`Close ${tab.name}`}
          >
            <X className="size-3.5 text-muted-foreground" />
          </button>
        </div>
      ))}
    </div>
  )
}
