'use client'

import { useState } from 'react'
import {
  ChevronDown,
  ChevronRight,
  FileText,
  Layout,
  Users,
  Layers,
  Palette,
  Code2,
  AlertTriangle,
} from 'lucide-react'
import type { RequirementsDoc, WireframeSpec, Feature, UserPersona, PageRoute } from '@/types/api.types'

type TabType = 'requirements' | 'architecture' | 'raw'

interface SpecViewerProps {
  requirementsSpec?: RequirementsDoc | Record<string, unknown> | null
  architectureSpec?: WireframeSpec | Record<string, unknown> | null
  className?: string
}

/**
 * SpecViewer — Renders requirements and architecture specifications.
 * 
 * Displays structured data from Research Agent (requirements_spec) and
 * Wireframe Agent (architecture_spec) with collapsible sections and tabs.
 */
export function SpecViewer({ requirementsSpec, architectureSpec, className = '' }: SpecViewerProps) {
  const [activeTab, setActiveTab] = useState<TabType>('requirements')
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set(['features', 'audience', 'pages', 'state'])
  )

  const toggleSection = (section: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev)
      if (next.has(section)) {
        next.delete(section)
      } else {
        next.add(section)
      }
      return next
    })
  }

  const hasRequirements = requirementsSpec && Object.keys(requirementsSpec).length > 0
  const hasArchitecture = architectureSpec && Object.keys(architectureSpec).length > 0
  const hasContent = hasRequirements || hasArchitecture

  const req = requirementsSpec as RequirementsDoc | undefined
  const arch = architectureSpec as WireframeSpec | undefined

  return (
    <div className={`rounded-lg border bg-card overflow-hidden ${className}`}>
      {/* Tabs */}
      <div className="flex border-b border-border bg-muted/30">
        <TabButton
          active={activeTab === 'requirements'}
          onClick={() => setActiveTab('requirements')}
          icon={<FileText className="size-4" />}
          label="Requirements"
          disabled={!hasRequirements}
        />
        <TabButton
          active={activeTab === 'architecture'}
          onClick={() => setActiveTab('architecture')}
          icon={<Layout className="size-4" />}
          label="Architecture"
          disabled={!hasArchitecture}
        />
        <TabButton
          active={activeTab === 'raw'}
          onClick={() => setActiveTab('raw')}
          icon={<Code2 className="size-4" />}
          label="Raw JSON"
        />
      </div>

      {/* Content */}
      <div className="p-4 max-h-[600px] overflow-y-auto custom-scrollbar">
        {!hasContent ? (
          <EmptyState />
        ) : activeTab === 'requirements' && req ? (
          <RequirementsView
            spec={req}
            expandedSections={expandedSections}
            toggleSection={toggleSection}
          />
        ) : activeTab === 'architecture' && arch ? (
          <ArchitectureView
            spec={arch}
            expandedSections={expandedSections}
            toggleSection={toggleSection}
          />
        ) : activeTab === 'raw' ? (
          <RawJsonView
            requirements={requirementsSpec}
            architecture={architectureSpec}
          />
        ) : (
          <EmptyState message="No data available for this tab." />
        )}
      </div>
    </div>
  )
}

// ── Tab Button ──
function TabButton({
  active,
  onClick,
  icon,
  label,
  disabled = false,
}: {
  active: boolean
  onClick: () => void
  icon: React.ReactNode
  label: string
  disabled?: boolean
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors border-b-2 -mb-px ${
        active
          ? 'border-cf-primary text-foreground bg-background'
          : disabled
          ? 'border-transparent text-muted-foreground/50 cursor-not-allowed'
          : 'border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/50'
      }`}
    >
      {icon}
      {label}
    </button>
  )
}

// ── Empty State ──
function EmptyState({ message = 'Run the Research Agent to generate specifications.' }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="size-12 rounded-full bg-muted flex items-center justify-center mb-4">
        <FileText className="size-6 text-muted-foreground" />
      </div>
      <p className="text-sm text-muted-foreground max-w-xs">{message}</p>
    </div>
  )
}

// ── Collapsible Section ──
function Section({
  id,
  title,
  icon,
  expanded,
  onToggle,
  children,
  badge,
}: {
  id: string
  title: string
  icon: React.ReactNode
  expanded: boolean
  onToggle: () => void
  children: React.ReactNode
  badge?: string | number
}) {
  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-3 p-3 bg-muted/30 hover:bg-muted/50 transition-colors text-left"
      >
        {expanded ? (
          <ChevronDown className="size-4 text-muted-foreground shrink-0" />
        ) : (
          <ChevronRight className="size-4 text-muted-foreground shrink-0" />
        )}
        <span className="text-muted-foreground">{icon}</span>
        <span className="text-sm font-medium text-foreground flex-1">{title}</span>
        {badge !== undefined && (
          <span className="text-xs bg-muted px-2 py-0.5 rounded-full text-muted-foreground">
            {badge}
          </span>
        )}
      </button>
      {expanded && <div className="p-3 border-t border-border">{children}</div>}
    </div>
  )
}

// ── Requirements View ──
function RequirementsView({
  spec,
  expandedSections,
  toggleSection,
}: {
  spec: RequirementsDoc
  expandedSections: Set<string>
  toggleSection: (s: string) => void
}) {
  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="space-y-2">
        <h2 className="text-xl font-bold text-foreground">{spec.app_name || 'Untitled App'}</h2>
        {spec.elevator_pitch && (
          <p className="text-sm text-muted-foreground leading-relaxed">{spec.elevator_pitch}</p>
        )}
      </div>

      {/* Target Audience */}
      {spec.target_audience && spec.target_audience.length > 0 && (
        <Section
          id="audience"
          title="Target Audience"
          icon={<Users className="size-4" />}
          expanded={expandedSections.has('audience')}
          onToggle={() => toggleSection('audience')}
          badge={spec.target_audience.length}
        >
          <div className="space-y-3">
            {spec.target_audience.map((persona, i) => (
              <PersonaCard key={i} persona={persona} />
            ))}
          </div>
        </Section>
      )}

      {/* Core Features */}
      {spec.core_features && spec.core_features.length > 0 && (
        <Section
          id="features"
          title="Core Features"
          icon={<Layers className="size-4" />}
          expanded={expandedSections.has('features')}
          onToggle={() => toggleSection('features')}
          badge={spec.core_features.length}
        >
          <div className="space-y-3">
            {spec.core_features.map((feature, i) => (
              <FeatureCard key={i} feature={feature} />
            ))}
          </div>
        </Section>
      )}

      {/* Tech Stack */}
      {spec.recommended_stack && Object.keys(spec.recommended_stack).length > 0 && (
        <Section
          id="stack"
          title="Recommended Stack"
          icon={<Code2 className="size-4" />}
          expanded={expandedSections.has('stack')}
          onToggle={() => toggleSection('stack')}
        >
          <div className="grid grid-cols-2 gap-2">
            {Object.entries(spec.recommended_stack).map(([key, value]) => (
              <div key={key} className="flex items-center gap-2 p-2 bg-muted/50 rounded">
                <span className="text-xs font-medium text-muted-foreground uppercase">{key}:</span>
                <span className="text-sm text-foreground">{value}</span>
              </div>
            ))}
          </div>
        </Section>
      )}

      {/* Technical Constraints */}
      {spec.technical_constraints && spec.technical_constraints.length > 0 && (
        <Section
          id="constraints"
          title="Technical Constraints"
          icon={<AlertTriangle className="size-4" />}
          expanded={expandedSections.has('constraints')}
          onToggle={() => toggleSection('constraints')}
          badge={spec.technical_constraints.length}
        >
          <ul className="space-y-2">
            {spec.technical_constraints.map((constraint, i) => (
              <li key={i} className="flex items-start gap-2 text-sm">
                <AlertTriangle className="size-4 text-amber-500 shrink-0 mt-0.5" />
                <span className="text-foreground">{constraint}</span>
              </li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  )
}

// ── Persona Card ──
function PersonaCard({ persona }: { persona: UserPersona }) {
  return (
    <div className="p-3 bg-muted/30 rounded-lg border border-border">
      <div className="flex items-center gap-2 mb-2">
        <div className="size-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold">
          {persona.name?.charAt(0) || 'U'}
        </div>
        <div>
          <h4 className="text-sm font-medium text-foreground">{persona.name || 'User'}</h4>
        </div>
      </div>
      {persona.description && (
        <p className="text-xs text-muted-foreground mb-2">{persona.description}</p>
      )}
      {persona.pain_points && persona.pain_points.length > 0 && (
        <div className="mt-2">
          <p className="text-xs font-medium text-muted-foreground mb-1">Pain Points:</p>
          <ul className="space-y-1">
            {persona.pain_points.map((point, i) => (
              <li key={i} className="text-xs text-foreground flex items-start gap-1.5">
                <AlertTriangle className="size-3 text-amber-500 shrink-0 mt-0.5" />
                {point}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

// ── Feature Card ──
function FeatureCard({ feature }: { feature: Feature }) {
  const priorityColors: Record<string, string> = {
    'must-have': 'bg-red-500/10 text-red-500 border-red-500/20',
    'should-have': 'bg-amber-500/10 text-amber-500 border-amber-500/20',
    'nice-to-have': 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  }

  const defaultColor = 'bg-muted text-muted-foreground border-border'

  return (
    <div className="p-3 bg-muted/30 rounded-lg border border-border">
      <div className="flex items-start justify-between gap-2 mb-2">
        <h4 className="text-sm font-medium text-foreground">{feature.name}</h4>
        <span
          className={`text-xs px-2 py-0.5 rounded border ${
            priorityColors[feature.priority] || defaultColor
          }`}
        >
          {feature.priority}
        </span>
      </div>
      <p className="text-xs text-muted-foreground mb-2">{feature.description}</p>
      {feature.user_stories && feature.user_stories.length > 0 && (
        <div className="space-y-1">
          {feature.user_stories.slice(0, 3).map((story, i) => (
            <p key={i} className="text-xs text-foreground/80 italic">
              &ldquo;{story}&rdquo;
            </p>
          ))}
          {feature.user_stories.length > 3 && (
            <p className="text-xs text-muted-foreground">
              +{feature.user_stories.length - 3} more stories
            </p>
          )}
        </div>
      )}
    </div>
  )
}

// ── Architecture View ──
function ArchitectureView({
  spec,
  expandedSections,
  toggleSection,
}: {
  spec: WireframeSpec
  expandedSections: Set<string>
  toggleSection: (s: string) => void
}) {
  return (
    <div className="space-y-4">
      {/* Site Map / Pages */}
      {spec.site_map && spec.site_map.length > 0 && (
        <Section
          id="pages"
          title="Site Map"
          icon={<Layout className="size-4" />}
          expanded={expandedSections.has('pages')}
          onToggle={() => toggleSection('pages')}
          badge={spec.site_map.length}
        >
          <div className="space-y-2">
            {spec.site_map.map((page, i) => (
              <PageCard key={i} page={page} />
            ))}
          </div>
        </Section>
      )}

      {/* Global State */}
      {spec.global_state_needs && spec.global_state_needs.length > 0 && (
        <Section
          id="state"
          title="Global State"
          icon={<Layers className="size-4" />}
          expanded={expandedSections.has('state')}
          onToggle={() => toggleSection('state')}
          badge={spec.global_state_needs.length}
        >
          <ul className="space-y-1">
            {spec.global_state_needs.map((state, i) => (
              <li key={i} className="text-sm text-foreground flex items-center gap-2">
                <div className="size-1.5 rounded-full bg-cf-primary" />
                {state}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {/* Theme Colors */}
      {spec.theme_colors && Object.keys(spec.theme_colors).length > 0 && (
        <Section
          id="theme"
          title="Theme Colors"
          icon={<Palette className="size-4" />}
          expanded={expandedSections.has('theme')}
          onToggle={() => toggleSection('theme')}
        >
          <div className="flex flex-wrap gap-2">
            {Object.entries(spec.theme_colors).map(([name, color]) => (
              <div
                key={name}
                className="flex items-center gap-2 px-3 py-1.5 bg-muted/50 rounded-lg border border-border"
              >
                <div
                  className="size-4 rounded border border-border"
                  style={{ backgroundColor: color }}
                />
                <span className="text-xs text-muted-foreground">{name}</span>
                <code className="text-xs font-mono text-foreground">{color}</code>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  )
}

// ── Page Card ──
function PageCard({ page }: { page: PageRoute }) {
  return (
    <div className="p-3 bg-muted/30 rounded-lg border border-border">
      <div className="flex items-center gap-2 mb-2">
        <code className="text-xs font-mono bg-muted px-2 py-0.5 rounded text-cf-primary">
          {page.path}
        </code>
        <span className="text-sm font-medium text-foreground">{page.name}</span>
      </div>
      {page.layout && (
        <p className="text-xs text-muted-foreground mb-2">Layout: {page.layout}</p>
      )}
      {page.components && page.components.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {page.components.map((comp, i) => (
            <span
              key={i}
              className="text-xs bg-muted px-2 py-0.5 rounded text-foreground"
            >
              {comp.name}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}

// ── Raw JSON View ──
function RawJsonView({
  requirements,
  architecture,
}: {
  requirements?: unknown
  architecture?: unknown
}) {
  const combined = {
    requirements_spec: requirements || null,
    architecture_spec: architecture || null,
  }

  return (
    <div className="relative">
      <pre className="text-xs font-mono text-foreground bg-muted/30 p-4 rounded-lg overflow-x-auto max-h-[500px]">
        {JSON.stringify(combined, null, 2)}
      </pre>
    </div>
  )
}

