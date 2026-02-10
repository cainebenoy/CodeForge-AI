'use client'

import { useState, useMemo } from 'react'
import {
  FolderOpen,
  Folder,
  FileCode,
  FileText,
  FileJson,
  FileCog,
  ChevronDown,
  ChevronRight,
  FolderPlus,
  FilePlus,
} from 'lucide-react'
import { useBuilderStore } from '@/store/useBuilderStore'

/* ─── File tree node ─── */
interface TreeNode {
  name: string
  type: 'file' | 'folder'
  path: string
  children?: TreeNode[]
  icon?: string
}

const iconColorMap: Record<string, string> = {
  tsx: 'text-blue-400',
  ts: 'text-purple-400',
  jsx: 'text-blue-400',
  js: 'text-yellow-400',
  css: 'text-yellow-400 dark:text-yellow-400',
  json: 'text-orange-400 dark:text-orange-400',
  md: 'text-muted-foreground',
  config: 'text-muted-foreground',
}

function getIconType(name: string): string {
  const ext = name.split('.').pop()?.toLowerCase() ?? ''
  if (['tsx', 'ts', 'jsx', 'js', 'css', 'json', 'md'].includes(ext)) return ext
  if (name.includes('config') || name.includes('.env')) return 'config'
  return 'file'
}

function FileIcon({ iconType }: { iconType: string }) {
  const color = iconColorMap[iconType] ?? 'text-muted-foreground'
  switch (iconType) {
    case 'tsx':
    case 'ts':
    case 'jsx':
    case 'js':
      return <FileCode className={`size-4 ${color}`} />
    case 'css':
      return <FileText className={`size-4 ${color}`} />
    case 'json':
      return <FileJson className={`size-4 ${color}`} />
    case 'config':
      return <FileCog className={`size-4 ${color}`} />
    default:
      return <FileText className={`size-4 ${color}`} />
  }
}

/** Build a tree structure from flat file paths */
function buildTree(paths: string[]): TreeNode[] {
  const root: TreeNode[] = []

  for (const filePath of paths.sort()) {
    const parts = filePath.split('/')
    let current = root

    for (let i = 0; i < parts.length; i++) {
      const name = parts[i]
      const isFile = i === parts.length - 1
      const existingNode = current.find((n) => n.name === name)

      if (existingNode) {
        current = existingNode.children ?? []
      } else {
        const newNode: TreeNode = {
          name,
          type: isFile ? 'file' : 'folder',
          path: parts.slice(0, i + 1).join('/'),
          icon: isFile ? getIconType(name) : undefined,
          children: isFile ? undefined : [],
        }
        current.push(newNode)
        if (!isFile) current = newNode.children!
      }
    }
  }

  return root
}

function TreeItem({
  node,
  depth = 0,
}: {
  node: TreeNode
  depth?: number
}) {
  const [open, setOpen] = useState(node.type === 'folder')
  const activeFile = useBuilderStore((s) => s.activeFile)
  const setActiveFile = useBuilderStore((s) => s.setActiveFile)

  const isFolder = node.type === 'folder'
  const isActive = activeFile === node.path

  const handleClick = () => {
    if (isFolder) {
      setOpen(!open)
    } else {
      setActiveFile(node.path)
    }
  }

  return (
    <>
      <div
        onClick={handleClick}
        className={`flex items-center gap-2 py-1 px-2 rounded cursor-pointer group border-l-2 transition-colors ${
          isActive
            ? 'bg-cf-primary/10 dark:bg-muted border-cf-primary text-foreground font-medium'
            : 'border-transparent hover:bg-muted text-muted-foreground hover:text-foreground'
        }`}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
      >
        {isFolder && (
          open ? (
            <ChevronDown className="size-3.5 text-muted-foreground" />
          ) : (
            <ChevronRight className="size-3.5 text-muted-foreground" />
          )
        )}
        {isFolder ? (
          open ? (
            <FolderOpen className="size-4 text-blue-400" />
          ) : (
            <Folder className="size-4 text-muted-foreground" />
          )
        ) : (
          <FileIcon iconType={node.icon ?? 'file'} />
        )}
        <span className="text-sm truncate">{node.name}</span>
      </div>

      {isFolder && open && node.children && (
        <div className={depth > 0 ? 'border-l border-border ml-4' : ''}>
          {node.children.map((child) => (
            <TreeItem key={child.path} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </>
  )
}

/**
 * BuilderFileTree — File explorer sidebar for the Builder IDE.
 * Reads files from Zustand store (synced from API via page.tsx).
 */
export function BuilderFileTree({ projectId }: { projectId: string }) {
  const generatedFiles = useBuilderStore((s) => s.generatedFiles)
  const filePaths = useMemo(() => Object.keys(generatedFiles), [generatedFiles])
  const tree = useMemo(() => buildTree(filePaths), [filePaths])

  return (
    <aside className="w-64 shrink-0 border-r border-border bg-muted/30 dark:bg-background flex flex-col">
      {/* Header */}
      <div className="p-3 border-b border-border/50 flex items-center justify-between">
        <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Explorer
        </span>
        <div className="flex gap-1">
          <button
            className="text-muted-foreground hover:text-foreground p-1 rounded hover:bg-muted"
            aria-label="New folder"
          >
            <FolderPlus className="size-3.5" />
          </button>
          <button
            className="text-muted-foreground hover:text-foreground p-1 rounded hover:bg-muted"
            aria-label="New file"
          >
            <FilePlus className="size-3.5" />
          </button>
        </div>
      </div>

      {/* Tree */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-2">
        {tree.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <p className="text-xs text-muted-foreground">
              No files yet. Run an agent to generate code.
            </p>
          </div>
        ) : (
          <div className="flex flex-col gap-0.5">
            {tree.map((node) => (
              <TreeItem key={node.path} node={node} depth={0} />
            ))}
          </div>
        )}
      </div>

      {/* Outline / Timeline collapse sections (light mode) */}
      <div className="border-t border-border block dark:hidden">
        {['OUTLINE', 'TIMELINE'].map((label) => (
          <div
            key={label}
            className="flex items-center gap-1 px-4 py-2 text-xs font-semibold text-muted-foreground hover:text-foreground cursor-pointer"
          >
            <ChevronRight className="size-3.5" />
            {label}
          </div>
        ))}
      </div>
    </aside>
  )
}
