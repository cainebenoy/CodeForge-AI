'use client'

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

/* ─── Demo file tree data ─── */
interface TreeNode {
  name: string
  type: 'file' | 'folder'
  children?: TreeNode[]
  icon?: 'tsx' | 'css' | 'json' | 'ts' | 'config'
  active?: boolean
}

const demoTree: TreeNode[] = [
  { name: 'public', type: 'folder' },
  {
    name: 'src',
    type: 'folder',
    children: [
      { name: 'App.tsx', type: 'file', icon: 'tsx', active: true },
      { name: 'index.css', type: 'file', icon: 'css' },
      { name: 'vite-env.d.ts', type: 'file', icon: 'ts' },
      { name: 'main.tsx', type: 'file', icon: 'tsx' },
      { name: 'components', type: 'folder' },
      { name: 'hooks', type: 'folder' },
    ],
  },
  { name: 'package.json', type: 'file', icon: 'json' },
  { name: 'tsconfig.json', type: 'file', icon: 'config' },
  { name: 'vite.config.ts', type: 'file', icon: 'config' },
]

const iconColorMap: Record<string, string> = {
  tsx: 'text-blue-400',
  css: 'text-yellow-400 dark:text-yellow-400',
  ts: 'text-purple-400',
  json: 'text-orange-400 dark:text-orange-400',
  config: 'text-muted-foreground',
}

function FileIcon({ iconType }: { iconType?: string }) {
  const color = iconType ? iconColorMap[iconType] ?? 'text-muted-foreground' : 'text-muted-foreground'
  switch (iconType) {
    case 'tsx':
    case 'ts':
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

function TreeItem({
  node,
  depth = 0,
}: {
  node: TreeNode
  depth?: number
}) {
  const isFolder = node.type === 'folder'
  const isOpen = isFolder && node.children
  const isActive = node.active

  return (
    <>
      <div
        className={`flex items-center gap-2 py-1 px-2 rounded cursor-pointer group border-l-2 transition-colors ${
          isActive
            ? 'bg-cf-primary/10 dark:bg-muted border-cf-primary text-foreground font-medium'
            : 'border-transparent hover:bg-muted text-muted-foreground hover:text-foreground'
        }`}
        style={{ paddingLeft: `${depth * 12 + 8}px` }}
      >
        {isFolder && (
          isOpen ? (
            <ChevronDown className="size-3.5 text-muted-foreground" />
          ) : (
            <ChevronRight className="size-3.5 text-muted-foreground" />
          )
        )}
        {isFolder ? (
          isOpen ? (
            <FolderOpen className="size-4 text-blue-400" />
          ) : (
            <Folder className="size-4 text-muted-foreground" />
          )
        ) : (
          <FileIcon iconType={node.icon} />
        )}
        <span className="text-sm truncate">{node.name}</span>
      </div>

      {isOpen && node.children && (
        <div className={depth > 0 ? 'border-l border-border ml-4' : ''}>
          {node.children.map((child) => (
            <TreeItem key={child.name} node={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </>
  )
}

/**
 * BuilderFileTree — File explorer sidebar for the Builder IDE.
 */
export function BuilderFileTree() {
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
        <div className="mb-1">
          <div className="flex items-center gap-1 py-1 px-2 rounded cursor-pointer hover:bg-muted group">
            <ChevronDown className="size-3.5 text-muted-foreground" />
            <span className="text-sm font-medium text-foreground">my-app</span>
          </div>
          <div className="pl-2 flex flex-col gap-0.5 mt-1">
            {demoTree.map((node) => (
              <TreeItem key={node.name} node={node} depth={1} />
            ))}
          </div>
        </div>
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
