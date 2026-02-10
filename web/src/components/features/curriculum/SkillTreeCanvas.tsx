'use client'

import {
  Flag,
  Code2,
  Database,
  Blocks,
  Lock,
  Plus,
  Minus,
  Maximize2,
  CheckCircle,
  LayoutGrid,
  Columns2,
  Smartphone,
} from 'lucide-react'

/* ═══════════════════════════════════════════
   DARK-MODE CANVAS — Circular nodes + SVG
   ═══════════════════════════════════════════ */
function DarkCanvas() {
  return (
    <main className="flex-1 relative overflow-hidden flex items-center justify-center cursor-grab active:cursor-grabbing">
      {/* Grid background */}
      <div className="absolute inset-0 bg-zinc-950 bg-[size:40px_40px] bg-[image:linear-gradient(to_right,#27272a_1px,transparent_1px),linear-gradient(to_bottom,#27272a_1px,transparent_1px)] opacity-[0.07] pointer-events-none" />
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-zinc-950 pointer-events-none" />

      {/* Canvas container */}
      <div className="relative w-[1200px] h-[800px] transform scale-[0.7] sm:scale-90 lg:scale-100 transition-transform duration-500">
        {/* SVG connections */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none z-0 opacity-60">
          <defs>
            <linearGradient id="lg-c" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#13ec6d" stopOpacity="0.6" />
              <stop offset="100%" stopColor="#13ec6d" stopOpacity="0.2" />
            </linearGradient>
            <linearGradient id="lg-a" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#13ec6d" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#a78bfa" stopOpacity="0.6" />
            </linearGradient>
          </defs>
          {/* Start → Fundamentals */}
          <path className="circuit-line" d="M100 400 L200 400" fill="none" stroke="#13ec6d" strokeWidth={2} />
          {/* Fundamentals → Frontend */}
          <path d="M264 400 L320 400 L350 300 L450 300" fill="none" stroke="url(#lg-c)" strokeWidth={2} />
          {/* Fundamentals → Backend */}
          <path d="M264 400 L320 400 L350 500 L450 500" fill="none" stroke="#13ec6d" strokeWidth={2} opacity={0.3} />
          {/* Frontend → React (active) */}
          <path className="circuit-line" d="M514 300 L650 300" fill="none" stroke="url(#lg-a)" strokeWidth={2} />
          {/* React → locked branches */}
          <path d="M714 300 L760 300 L790 200 L850 200" fill="none" stroke="#27272a" strokeWidth={2} />
          <path d="M714 300 L760 300 L790 400 L850 400" fill="none" stroke="#27272a" strokeWidth={2} />
        </svg>

        {/* ── Nodes ── */}
        {/* 1 – Orientation (completed) */}
        <DarkNode
          top={400} left={232}
          icon={<Flag className="size-5" />}
          label="Orientation"
          variant="completed"
        />

        {/* 2 – Web Basics (completed) */}
        <DarkNode
          top={300} left={482}
          icon={<Code2 className="size-5" />}
          label="Web Basics"
          variant="completed"
        />

        {/* 3 – Database Design (pending) */}
        <DarkNode
          top={500} left={482}
          icon={<Database className="size-5" />}
          label="Database Design"
          variant="pending"
        />

        {/* 4 – React Foundations (active) */}
        <DarkNode
          top={300} left={682}
          icon={<Blocks className="size-8" />}
          label="React Foundations"
          variant="active"
          large
        />

        {/* 5 – State Management (locked) */}
        <DarkNode top={200} left={882} icon={<Lock className="size-5" />} label="State Management" variant="locked" />

        {/* 6 – API Integration (locked) */}
        <DarkNode top={400} left={882} icon={<Lock className="size-5" />} label="API Integration" variant="locked" />
      </div>

      {/* Zoom controls */}
      <div className="absolute bottom-8 left-8 flex gap-2">
        {[
          { icon: <Plus className="size-4" />, label: 'Zoom In' },
          { icon: <Minus className="size-4" />, label: 'Zoom Out' },
          { icon: <Maximize2 className="size-4" />, label: 'Fit' },
        ].map(({ icon, label }) => (
          <button
            key={label}
            aria-label={label}
            className="size-10 rounded bg-zinc-800 border border-border text-foreground hover:bg-zinc-700 flex items-center justify-center"
          >
            {icon}
          </button>
        ))}
      </div>
    </main>
  )
}

/* ── Dark-mode Node ── */
function DarkNode({
  top,
  left,
  icon,
  label,
  variant,
  large,
}: {
  top: number
  left: number
  icon: React.ReactNode
  label: string
  variant: 'completed' | 'active' | 'pending' | 'locked'
  large?: boolean
}) {
  const size = large ? 'size-20' : 'size-16'
  const borderSize = large ? 'border-[3px]' : 'border-2'

  const styles: Record<string, { border: string; shadow: string; text: string; labelCls: string }> = {
    completed: {
      border: 'border-cf-primary',
      shadow: 'shadow-[0_0_15px_rgba(19,236,109,0.3)]',
      text: 'text-cf-primary',
      labelCls: 'text-cf-primary bg-zinc-900/80 border-cf-primary/20',
    },
    active: {
      border: 'border-violet-400',
      shadow: 'shadow-[0_0_20px_rgba(167,139,250,0.4)]',
      text: 'text-violet-400',
      labelCls: 'text-violet-400 bg-zinc-900/80 border-violet-400/30 shadow-[0_4px_20px_rgba(0,0,0,0.5)]',
    },
    pending: {
      border: 'border-cf-primary/30',
      shadow: '',
      text: 'text-cf-primary/50',
      labelCls: 'text-muted-foreground bg-zinc-900/80 border-zinc-800',
    },
    locked: {
      border: 'border-zinc-700',
      shadow: '',
      text: 'text-zinc-600',
      labelCls: 'text-zinc-600',
    },
  }

  const s = styles[variant]

  return (
    <div
      className={`absolute -translate-x-1/2 -translate-y-1/2 flex flex-col items-center gap-3 z-10 group cursor-pointer
        ${variant === 'locked' ? 'opacity-50' : variant === 'pending' ? 'opacity-80' : ''}`}
      style={{ top: `${top}px`, left: `${left}px` }}
    >
      {variant === 'active' && (
        <div className="absolute inset-0 rounded-full pulse-ring z-0" />
      )}
      <div
        className={`${size} rounded-full bg-zinc-900 ${borderSize} ${s.border} ${s.shadow} flex items-center justify-center ${s.text} relative z-10 transition-transform group-hover:scale-110`}
      >
        {icon}
      </div>
      <span
        className={`font-mono text-xs font-bold px-2 py-1 rounded backdrop-blur-md border ${s.labelCls}
          ${large ? 'text-sm px-3 py-1.5' : ''}`}
      >
        {label}
      </span>
    </div>
  )
}

/* ═══════════════════════════════════════════
   LIGHT-MODE CANVAS — Card nodes + CSS lines
   ═══════════════════════════════════════════ */
function LightCanvas() {
  return (
    <main className="flex-1 bg-zinc-50 bg-[size:40px_40px] bg-[image:linear-gradient(to_right,#e4e4e7_1px,transparent_1px),linear-gradient(to_bottom,#e4e4e7_1px,transparent_1px)] relative overflow-auto cursor-grab active:cursor-grabbing p-10">
      {/* Grid label */}
      <div className="absolute top-4 left-4 border border-border px-2 py-1 bg-white/50 backdrop-blur-sm rounded-sm">
        <span className="text-[10px] font-mono text-muted-foreground tracking-widest">GRID SYSTEM V1.0</span>
      </div>

      {/* Skill tree */}
      <div className="relative min-w-[1000px] min-h-[800px] flex flex-col items-center pt-10">
        {/* Level 1: Foundation */}
        <div className="relative z-10 flex flex-col items-center gap-2 mb-20">
          <LightCard
            title="HTML5 Foundation"
            description="Semantic markup and document structure."
            variant="completed"
            connectorBelow
          />
        </div>

        {/* Level 2: Branching */}
        <div className="relative z-10 grid grid-cols-3 gap-32 mb-20 w-full max-w-5xl justify-items-center">
          {/* Connecting lines */}
          <div className="absolute -top-20 left-[18%] right-[18%] h-px bg-muted-foreground/40" />
          <div className="absolute -top-20 left-[18%] w-px h-20 bg-muted-foreground/40" />
          <div className="absolute -top-20 left-1/2 w-px h-20 bg-muted-foreground/40" />
          <div className="absolute -top-20 right-[18%] w-px h-20 bg-muted-foreground/40" />

          <LightCard
            title="CSS Basics"
            description="Box model, typography, and colors."
            variant="completed"
          />
          <LightCard
            title="CSS Grid Systems"
            description=""
            variant="active"
            progress={33}
            connectorBelow
            icon={<LayoutGrid className="size-5" />}
          />
          <LightCard
            title="Flexbox"
            description="One-dimensional layout method."
            variant="locked"
            icon={<Columns2 className="size-5" />}
          />
        </div>

        {/* Level 3 */}
        <div className="relative z-10 flex flex-col items-center gap-2">
          <LightCard
            title="Responsive Design"
            description="Media queries and mobile-first approach."
            variant="locked"
            icon={<Smartphone className="size-5" />}
          />
        </div>
      </div>
    </main>
  )
}

/* ── Light-mode Card Node ── */
function LightCard({
  title,
  description,
  variant,
  progress,
  connectorBelow,
  icon,
}: {
  title: string
  description: string
  variant: 'completed' | 'active' | 'locked'
  progress?: number
  connectorBelow?: boolean
  icon?: React.ReactNode
}) {
  const isActive = variant === 'active'
  const isLocked = variant === 'locked'
  const isCompleted = variant === 'completed'

  return (
    <div
      className={`relative flex flex-col gap-2 cursor-pointer transition-all group
        ${isActive
          ? 'w-56 bg-white border-2 border-violet-600 rounded-lg shadow-lg p-5 z-20 ring-4 ring-violet-600/10 transform scale-105'
          : isLocked
            ? 'w-48 bg-white/50 border border-border rounded-lg p-4 opacity-70 grayscale'
            : 'w-48 bg-white border border-border rounded-lg shadow-sm p-4 hover:border-muted-foreground/50'
        }`}
    >
      {connectorBelow && (
        <div className={`absolute -bottom-20 left-1/2 w-px h-20 ${isActive ? 'bg-muted-foreground/30 border-l border-dashed border-muted-foreground/40' : 'bg-muted-foreground/40'}`} />
      )}

      <div className="flex justify-between items-start">
        {isCompleted && <CheckCircle className="size-5 text-emerald-600" />}
        {isActive && (
          <div className="bg-violet-600/10 p-1.5 rounded text-violet-600">
            {icon ?? <LayoutGrid className="size-5" />}
          </div>
        )}
        {isLocked && <Lock className="size-5 text-muted-foreground" />}

        {isCompleted && (
          <span className="text-[10px] font-mono text-emerald-600 bg-emerald-50 px-1 rounded">
            DONE
          </span>
        )}
        {isActive && (
          <span className="text-[10px] font-mono text-white bg-violet-600 px-1.5 py-0.5 rounded tracking-wide">
            CURRENT
          </span>
        )}
        {isLocked && (
          <span className="text-[10px] font-mono text-muted-foreground border border-border px-1 rounded">
            LOCKED
          </span>
        )}
      </div>

      <h3 className={`font-bold ${isActive ? 'text-lg leading-tight' : ''} ${isLocked ? 'text-muted-foreground' : 'text-foreground'}`}>
        {title}
      </h3>

      {description && (
        <p className={`text-xs line-clamp-2 ${isLocked ? 'text-muted-foreground/70' : 'text-muted-foreground'}`}>
          {description}
        </p>
      )}

      {isActive && progress !== undefined && (
        <div>
          <div className="w-full bg-muted h-1 mt-2 rounded-full overflow-hidden">
            <div className="bg-violet-600 h-full" style={{ width: `${progress}%` }} />
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-[10px] text-muted-foreground">Progress</span>
            <span className="text-[10px] font-bold text-foreground">{progress}%</span>
          </div>
        </div>
      )}
    </div>
  )
}

/* ═══════════════════════════════════════════
   PUBLIC EXPORT
   ═══════════════════════════════════════════ */
export function SkillTreeCanvas() {
  return (
    <>
      <div className="hidden dark:flex flex-1 min-h-0">
        <DarkCanvas />
      </div>
      <div className="flex dark:hidden flex-1 min-h-0">
        <LightCanvas />
      </div>
    </>
  )
}
