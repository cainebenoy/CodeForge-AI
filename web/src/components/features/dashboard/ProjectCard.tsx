import Link from 'next/link'
import {
  Clock,
  MoreVertical,
  Server,
  GraduationCap,
  Bot,
  Globe,
  BarChart3,
  Palette,
  Wrench,
  Code,
  TerminalSquare,
  Database,
  Brush,
  Layers,
  type LucideIcon,
} from 'lucide-react'

/* ─── Types ─── */
export type ProjectMode = 'builder' | 'student'

export type ProjectStatus =
  | 'Development'
  | 'Production'
  | 'Paused'
  | 'Planning'
  | 'In Review'

export interface ProjectCardProps {
  id: string
  title: string
  description: string
  mode: ProjectMode
  /** Time-ago string, e.g. "2h ago" */
  editedAt: string
  /** Gradient from/to classes for the icon square */
  gradient: string
  /** Lucide icon component */
  icon: LucideIcon
  /** Project status badge */
  status?: ProjectStatus
  /** Repo-style slug shown under title in light mode */
  slug?: string
  /** Avatar initials or colour classes */
  avatarColors?: string[]
  /** Tech icons shown at bottom in light mode */
  techIcons?: LucideIcon[]
}

/* ─── Helpers ─── */
const modeConfig = {
  builder: {
    badge: 'BUILDER',
    badgeBg:
      'bg-blue-100 dark:bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-200 dark:border-blue-500/20',
    stripe: 'from-blue-500 to-cyan-500',
  },
  student: {
    badge: 'STUDENT',
    badgeBg:
      'bg-violet-100 dark:bg-violet-500/10 text-violet-700 dark:text-violet-400 border-violet-200 dark:border-violet-500/20',
    stripe: 'from-violet-500 to-fuchsia-500',
  },
} as const

const statusColors: Record<ProjectStatus, string> = {
  Development:
    'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
  Production:
    'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300',
  Paused:
    'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300',
  Planning:
    'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300',
  'In Review':
    'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300',
}

/**
 * ProjectCard — renders a single project in the dashboard grid.
 * Adapts between dark-mode (simpler) and light-mode (richer) via Tailwind dark: variants.
 */
export function ProjectCard({
  id,
  title,
  description,
  mode,
  editedAt,
  gradient,
  icon: Icon,
  status,
  slug,
  avatarColors = [],
  techIcons = [],
}: ProjectCardProps) {
  const cfg = modeConfig[mode]
  const href =
    mode === 'builder'
      ? `/dashboard/builder/${id}`
      : `/dashboard/student/${id}`

  return (
    <Link
      href={href}
      className="group relative flex flex-col overflow-hidden rounded-lg border border-border bg-card p-6 transition-all duration-300 hover:shadow-xl hover:shadow-black/10 dark:hover:shadow-black/20 hover:border-muted-foreground/30 dark:hover:border-muted-foreground/20 cursor-pointer"
    >
      {/* Top stripe on hover */}
      <div
        className={`absolute top-0 left-0 w-full h-1 bg-gradient-to-r ${cfg.stripe} opacity-0 group-hover:opacity-100 transition-opacity`}
      />

      {/* ── Dark-mode layout ── */}
      <div className="dark:block hidden">
        <div className="flex justify-between items-start mb-3">
          <div className={`p-2 rounded-md bg-opacity-10 ${mode === 'builder' ? 'bg-blue-500/10 text-blue-400' : 'bg-violet-500/10 text-violet-400'} mb-2`}>
            <Icon className="size-6" />
          </div>
          <span
            className={`inline-flex items-center px-2 py-1 rounded text-[10px] font-medium font-mono tracking-wide border uppercase ${cfg.badgeBg}`}
          >
            {cfg.badge}
          </span>
        </div>

        <h3 className="text-lg font-bold text-foreground mb-2 group-hover:text-cf-primary transition-colors">
          {title}
        </h3>
        <p className="text-sm text-muted-foreground leading-relaxed line-clamp-2 mb-6 flex-grow">
          {description}
        </p>

        <div className="flex items-center justify-between pt-4 border-t border-border mt-auto">
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <Clock className="size-4" />
            Edited {editedAt}
          </div>
          <div className="flex -space-x-2">
            {avatarColors.map((color, i) => (
              <div
                key={i}
                className={`w-6 h-6 rounded-full ${color} border-2 border-card`}
              />
            ))}
          </div>
        </div>
      </div>

      {/* ── Light-mode layout ── */}
      <div className="block dark:hidden">
        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center gap-4">
            <div
              className={`h-12 w-12 rounded-lg bg-gradient-to-br ${gradient} flex items-center justify-center text-white shadow-sm`}
            >
              <Icon className="size-6" />
            </div>
            <div>
              <h3 className="text-base font-bold text-foreground leading-tight group-hover:text-blue-600 transition-colors">
                {title}
              </h3>
              {slug && (
                <p className="text-xs text-muted-foreground mt-1">{slug}</p>
              )}
            </div>
          </div>
          <button
            className="text-muted-foreground hover:text-foreground p-1 rounded-md hover:bg-muted transition-colors"
            onClick={(e) => e.preventDefault()}
            aria-label="More options"
          >
            <MoreVertical className="size-5" />
          </button>
        </div>

        <p className="text-sm text-muted-foreground line-clamp-2 mb-6 h-10">
          {description}
        </p>

        <div className="mt-auto flex items-center justify-between">
          {status && (
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${statusColors[status]}`}
            >
              {status}
            </span>
          )}
          <div className="flex items-center gap-2 text-muted-foreground text-xs">
            <Clock className="size-4" />
            {editedAt}
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-border/50 flex items-center gap-3">
          <div className="flex -space-x-2">
            {avatarColors.map((color, i) => (
              <div
                key={i}
                className={`h-6 w-6 rounded-full ${color} ring-2 ring-background flex items-center justify-center text-[10px] font-bold text-white`}
              />
            ))}
          </div>
          {techIcons.length > 0 && (
            <div className="flex items-center gap-2 ml-auto">
              {techIcons.map((TechIcon, i) => (
                <TechIcon key={i} className="size-[18px] text-muted-foreground" />
              ))}
            </div>
          )}
        </div>
      </div>
    </Link>
  )
}

/* ─── Convenience icon re-exports for usage in page ─── */
export {
  Server,
  GraduationCap,
  Bot,
  Globe,
  BarChart3,
  Palette,
  Wrench,
  Code,
  TerminalSquare,
  Database,
  Brush,
  Layers,
}
