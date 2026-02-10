'use client'

import { useState } from 'react'
import {
  Plus,
  Upload,
  ArrowUpDown,
  LayoutGrid,
  List,
  Server,
  GraduationCap,
  Code,
  Loader2,
  AlertCircle,
  type LucideIcon,
} from 'lucide-react'
import {
  ProjectCard,
  type ProjectCardProps,
} from '@/components/features/dashboard/ProjectCard'
import { CreateProjectCard } from '@/components/features/dashboard/CreateProjectCard'
import { CreateProjectModal } from '@/components/features/dashboard/CreateProjectModal'
import { useProjects } from '@/lib/hooks/use-project'
import { useDashboardRealtime } from '@/lib/hooks/use-realtime'
import type { Project, ProjectMode } from '@/types/api.types'

/* ─────────────────────────────────────────────
 * Map API Project → UI ProjectCardProps
 * ───────────────────────────────────────────── */
const modeIcons: Record<ProjectMode, LucideIcon> = {
  builder: Server,
  student: GraduationCap,
}

const modeGradients: Record<ProjectMode, string> = {
  builder: 'from-blue-500 to-indigo-600',
  student: 'from-violet-500 to-fuchsia-500',
}

const statusMap: Record<string, ProjectCardProps['status']> = {
  planning: 'Planning',
  'in-progress': 'Development',
  building: 'Development',
  completed: 'Production',
  archived: 'Paused',
}

function formatTimeAgo(dateString: string): string {
  const diff = Date.now() - new Date(dateString).getTime()
  const minutes = Math.floor(diff / 60_000)
  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  const hours = Math.floor(minutes / 60)
  if (hours < 24) return `${hours}h ago`
  const days = Math.floor(hours / 24)
  if (days < 7) return `${days}d ago`
  const weeks = Math.floor(days / 7)
  return `${weeks}w ago`
}

function toCardProps(project: Project): ProjectCardProps {
  return {
    id: project.id,
    title: project.title,
    description: project.description || 'No description provided.',
    mode: project.mode,
    editedAt: formatTimeAgo(project.updated_at),
    gradient: modeGradients[project.mode],
    icon: modeIcons[project.mode],
    status: statusMap[project.status] ?? 'Development',
    avatarColors: project.mode === 'builder' ? ['bg-blue-500'] : ['bg-violet-500'],
    techIcons: [Code],
  }
}

/* ─────────────────────────────────────────────
 * Dashboard Page
 * ───────────────────────────────────────────── */
export default function DashboardPage() {
  const [modalOpen, setModalOpen] = useState(false)
  const [page, setPage] = useState(1)
  const [modeFilter, setModeFilter] = useState<string | undefined>(undefined)
  const pageSize = 9

  // Real-time: auto-refresh when any project changes in the DB
  useDashboardRealtime()

  const {
    data,
    isLoading,
    isError,
    error,
  } = useProjects({ page, page_size: pageSize, mode: modeFilter })

  const projects = data?.items ?? []
  const total = data?.total ?? 0
  const hasMore = data?.has_more ?? false
  const showingFrom = projects.length ? (page - 1) * pageSize + 1 : 0
  const showingTo = showingFrom + projects.length - (projects.length ? 1 : 0)

  return (
    <main className="flex-1 w-full overflow-y-auto">
      <div className="mx-auto max-w-7xl px-6 py-10 md:px-10 md:py-8 flex flex-col gap-8">
        {/* ── Page Header ── */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground">
              Projects
            </h2>
            <p className="text-muted-foreground text-sm mt-1">
              Manage your workspaces and learning paths.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button className="hidden sm:flex items-center justify-center h-10 px-4 rounded-lg border border-border bg-background text-muted-foreground text-sm font-medium hover:bg-muted transition-colors">
              <Upload className="size-4 mr-2" />
              Import
            </button>
            <button
              onClick={() => setModalOpen(true)}
              className="flex items-center justify-center h-10 px-5 rounded-lg bg-cf-primary text-black text-sm font-bold shadow-sm hover:brightness-110 transition-colors active:scale-95"
            >
              <Plus className="size-5 mr-2" />
              New Project
            </button>
          </div>
        </div>

        {/* ── Filters & Controls ── */}
        <div className="flex flex-wrap items-center gap-3 pb-2 border-b border-border">
          <div className="flex items-center gap-2">
            <button
              onClick={() => { setModeFilter(undefined); setPage(1) }}
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                !modeFilter
                  ? 'bg-card border border-border text-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              All Projects
              <span className="bg-muted text-muted-foreground text-xs py-0.5 px-1.5 rounded-md">
                {total}
              </span>
            </button>
            <button
              onClick={() => { setModeFilter('builder'); setPage(1) }}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                modeFilter === 'builder'
                  ? 'bg-card border border-border text-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Builder
            </button>
            <button
              onClick={() => { setModeFilter('student'); setPage(1) }}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                modeFilter === 'student'
                  ? 'bg-card border border-border text-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              Student
            </button>
          </div>

          <div className="ml-auto flex items-center gap-2">
            <div className="h-4 w-px bg-border mx-2 hidden sm:block" />
            <button className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg hover:bg-muted text-muted-foreground text-sm font-medium transition-colors">
              <ArrowUpDown className="size-4" />
              Last Updated
            </button>
            <button className="p-1.5 rounded-lg hover:bg-muted text-muted-foreground transition-colors" aria-label="Grid view">
              <LayoutGrid className="size-5" />
            </button>
            <button className="p-1.5 rounded-lg text-muted-foreground/50 hover:text-muted-foreground transition-colors" aria-label="List view">
              <List className="size-5" />
            </button>
          </div>
        </div>

        {/* ── Content ── */}
        {isLoading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        ) : isError ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3 text-center">
            <AlertCircle className="size-10 text-red-500" />
            <p className="text-sm text-muted-foreground max-w-md">
              {error instanceof Error ? error.message : 'Failed to load projects. Please try again.'}
            </p>
          </div>
        ) : projects.length === 0 && !modeFilter ? (
          /* Empty state — no projects at all */
          <div className="flex flex-col items-center justify-center py-20 gap-4 text-center">
            <div className="w-16 h-16 rounded-full bg-muted flex items-center justify-center">
              <Server className="size-8 text-muted-foreground" />
            </div>
            <div>
              <p className="text-lg font-semibold text-foreground">No projects yet</p>
              <p className="text-sm text-muted-foreground mt-1">
                Create your first project to get started.
              </p>
            </div>
            <button
              onClick={() => setModalOpen(true)}
              className="flex items-center gap-2 px-5 py-2.5 rounded-lg bg-cf-primary text-black text-sm font-bold hover:brightness-110 transition-colors"
            >
              <Plus className="size-5" />
              New Project
            </button>
          </div>
        ) : (
          <>
            {/* ── Project Grid ── */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {projects.map((project) => (
                <ProjectCard key={project.id} {...toCardProps(project)} />
              ))}
              <CreateProjectCard onClick={() => setModalOpen(true)} />
            </div>

            {/* ── Pagination ── */}
            {total > pageSize && (
              <div className="flex items-center justify-between border-t border-border pt-6 pb-2">
                <p className="text-sm text-muted-foreground">
                  Showing{' '}
                  <span className="font-medium text-foreground">{showingFrom}</span> to{' '}
                  <span className="font-medium text-foreground">{showingTo}</span>{' '}
                  of{' '}
                  <span className="font-medium text-foreground">{total}</span> results
                </p>
                <div className="flex gap-2">
                  <button
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="px-3 py-2 rounded-lg border border-border bg-card text-muted-foreground text-sm font-medium disabled:opacity-50 hover:bg-muted transition-colors"
                  >
                    Previous
                  </button>
                  <button
                    disabled={!hasMore}
                    onClick={() => setPage((p) => p + 1)}
                    className="px-3 py-2 rounded-lg border border-border bg-card text-foreground text-sm font-medium disabled:opacity-50 hover:bg-muted transition-colors"
                  >
                    Next
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* ── Create Project Modal ── */}
      <CreateProjectModal open={modalOpen} onClose={() => setModalOpen(false)} />
    </main>
  )
}
