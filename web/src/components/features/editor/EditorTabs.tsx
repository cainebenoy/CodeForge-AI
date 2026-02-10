'use client'

import { useMemo } from 'react'
import { X, FileCode, FileText } from 'lucide-react'
import { useBuilderStore } from '@/store/useBuilderStore'

const iconColorMap: Record<string, string> = {
  tsx: 'text-blue-400',
  ts: 'text-purple-400',
  jsx: 'text-blue-400',
  js: 'text-yellow-400',
  css: 'text-yellow-400',
  json: 'text-orange-400',
}

function getExt(name: string): string {
  return name.split('.').pop()?.toLowerCase() ?? ''
}

function TabIcon({ name }: { name: string }) {
  const ext = getExt(name)
  const color = iconColorMap[ext] ?? 'text-muted-foreground'
  return ext === 'css' ? (
    <FileText className={`size-3.5 ${color}`} />
  ) : (
    <FileCode className={`size-3.5 ${color}`} />
  )
}

/**
 * EditorTabs — Tab bar above the code editor.
 * Reads open file tabs from the Zustand builder store.
 * Shows the active file's tab with a top accent border.
 */
export function EditorTabs({ projectId }: { projectId: string }) {
  const activeFile = useBuilderStore((s) => s.activeFile)
  const setActiveFile = useBuilderStore((s) => s.setActiveFile)
  const generatedFiles = useBuilderStore((s) => s.generatedFiles)

  // For now, show up to 6 files as tabs
  const openTabs = useMemo(() => {
    const paths = Object.keys(generatedFiles).slice(0, 6)
    // Ensure activeFile is in the tab list
    if (activeFile && !paths.includes(activeFile)) {
      paths.unshift(activeFile)
    }
    return paths
  }, [generatedFiles, activeFile])

  if (openTabs.length === 0) return null

  return (
    <div className="flex items-center bg-muted/50 dark:bg-background border-b border-border overflow-x-auto">
      {openTabs.map((filePath) => {
        const fileName = filePath.split('/').pop() ?? filePath
        const isActive = filePath === activeFile

        return (
          <div
            key={filePath}
            onClick={() => setActiveFile(filePath)}
            className={`flex items-center gap-2 px-4 py-2 text-sm min-w-[140px] justify-between group cursor-pointer transition-colors ${
              isActive
                ? 'bg-background dark:bg-black border-t-2 border-t-cf-primary text-foreground font-medium'
                : 'border-r border-border/50 text-muted-foreground hover:bg-muted/80 dark:hover:bg-muted/50'
            }`}
          >
            <div className="flex items-center gap-2">
              <TabIcon name={fileName} />
              <span className="truncate">{fileName}</span>
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation()
                // If closing active tab, switch to another
                if (isActive) {
                  const remaining = openTabs.filter((p) => p !== filePath)
                  setActiveFile(remaining[0] ?? null)
                }
              }}
              className="opacity-0 group-hover:opacity-100 hover:bg-muted rounded p-0.5 transition-all"
              aria-label={`Close ${fileName}`}
            >
              <X className="size-3.5 text-muted-foreground" />
            </button>
          </div>
        )
      })}
    </div>
  )
}
