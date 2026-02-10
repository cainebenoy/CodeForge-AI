import {
  Plus,
  Upload,
  ArrowUpDown,
  LayoutGrid,
  List,
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
} from 'lucide-react'
import {
  ProjectCard,
  type ProjectCardProps,
} from '@/components/features/dashboard/ProjectCard'
import { CreateProjectCard } from '@/components/features/dashboard/CreateProjectCard'

/* ─────────────────────────────────────────────
 * Demo data – will be replaced by Supabase query
 * ───────────────────────────────────────────── */
const projects: ProjectCardProps[] = [
  {
    id: 'ecommerce-backend',
    title: 'E-commerce Dashboard',
    description:
      'React-based admin panel for managing inventory, orders, and customer analytics.',
    mode: 'builder',
    editedAt: '2h ago',
    gradient: 'from-blue-500 to-indigo-600',
    icon: Server,
    status: 'Development',
    slug: 'codeforge/ecommerce-v2',
    avatarColors: ['bg-blue-500', 'bg-indigo-500'],
    techIcons: [Code, TerminalSquare],
  },
  {
    id: 'ai-chatbot',
    title: 'AI Chatbot Interface',
    description:
      'Client-facing chat interface powered by GPT-4 with streaming response support.',
    mode: 'builder',
    editedAt: '1d ago',
    gradient: 'from-emerald-400 to-green-600',
    icon: Bot,
    status: 'Production',
    slug: 'codeforge/ai-chat-ui',
    avatarColors: ['bg-green-500'],
    techIcons: [Database, Code],
  },
  {
    id: 'react-basics',
    title: 'React Basics Course',
    description:
      'Learning materials and exercises for React hooks, state management, and component lifecycles.',
    mode: 'student',
    editedAt: '1d ago',
    gradient: 'from-violet-500 to-fuchsia-500',
    icon: GraduationCap,
    status: 'Development',
    slug: 'codeforge/react-basics',
    avatarColors: ['bg-pink-500'],
    techIcons: [Code, Layers],
  },
  {
    id: 'internal-tools-api',
    title: 'Internal Tools API',
    description:
      'Legacy API service for employee directory and asset management.',
    mode: 'builder',
    editedAt: '5d ago',
    gradient: 'from-amber-400 to-orange-500',
    icon: Wrench,
    status: 'Paused',
    slug: 'codeforge/internal-api',
    avatarColors: ['bg-amber-500'],
    techIcons: [Database],
  },
  {
    id: 'portfolio-site-v2',
    title: 'Portfolio Site v2',
    description:
      'Redesigning personal portfolio using Next.js 14 and Tailwind CSS components.',
    mode: 'student',
    editedAt: '5d ago',
    gradient: 'from-purple-500 to-pink-500',
    icon: Palette,
    status: 'Planning',
    slug: 'codeforge/cosmos-ds',
    avatarColors: ['bg-orange-500', 'bg-purple-500'],
    techIcons: [Brush, Layers],
  },
  {
    id: 'sales-dashboard',
    title: 'Marketing Website',
    description:
      'Main landing page with Framer Motion animations and CMS integration.',
    mode: 'builder',
    editedAt: '1w ago',
    gradient: 'from-cyan-400 to-blue-500',
    icon: Globe,
    status: 'In Review',
    slug: 'codeforge/www',
    avatarColors: ['bg-teal-500'],
    techIcons: [Layers],
  },
]

export default function DashboardPage() {
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
            {/* Import button (light-mode extra action) */}
            <button className="hidden sm:flex items-center justify-center h-10 px-4 rounded-lg border border-border bg-background text-muted-foreground text-sm font-medium hover:bg-muted transition-colors">
              <Upload className="size-4 mr-2" />
              Import
            </button>
            <button className="flex items-center justify-center h-10 px-5 rounded-lg bg-cf-primary text-black text-sm font-bold shadow-sm hover:brightness-110 transition-colors active:scale-95">
              <Plus className="size-5 mr-2" />
              New Project
            </button>
          </div>
        </div>

        {/* ── Filters & Controls ── */}
        <div className="flex flex-wrap items-center gap-3 pb-2 border-b border-border">
          <div className="flex items-center gap-2">
            <button className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-card border border-border text-sm font-medium text-foreground hover:border-muted-foreground/40 transition-colors">
              All Projects
              <span className="bg-muted text-muted-foreground text-xs py-0.5 px-1.5 rounded-md">
                {projects.length}
              </span>
            </button>
            <button className="px-3 py-1.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
              Favorites
            </button>
            <button className="px-3 py-1.5 rounded-lg text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
              Archived
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

        {/* ── Project Grid ── */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <ProjectCard key={project.id} {...project} />
          ))}
          <CreateProjectCard />
        </div>

        {/* ── Pagination ── */}
        <div className="flex items-center justify-between border-t border-border pt-6 pb-2">
          <p className="text-sm text-muted-foreground">
            Showing{' '}
            <span className="font-medium text-foreground">1</span> to{' '}
            <span className="font-medium text-foreground">
              {projects.length}
            </span>{' '}
            of{' '}
            <span className="font-medium text-foreground">12</span> results
          </p>
          <div className="flex gap-2">
            <button
              disabled
              className="px-3 py-2 rounded-lg border border-border bg-card text-muted-foreground text-sm font-medium disabled:opacity-50"
            >
              Previous
            </button>
            <button className="px-3 py-2 rounded-lg border border-border bg-card text-foreground text-sm font-medium hover:bg-muted transition-colors">
              Next
            </button>
          </div>
        </div>
      </div>
    </main>
  )
}
