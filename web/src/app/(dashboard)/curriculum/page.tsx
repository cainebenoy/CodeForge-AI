import {
  SkillTreeHeader,
  SkillTreeCanvas,
  ModuleSidebar,
} from '@/components/features/curriculum'

/**
 * Skill Tree / Curriculum page.
 *
 * **Dark**: Full-bleed workspace — header, canvas with SVG circuit-line
 *           nodes (completed/active/pending/locked), right sidebar with glass panel.
 * **Light**: Header, card-based skill tree on dotted grid, white right sidebar.
 *
 * Route: /dashboard/curriculum
 */
export default function CurriculumPage() {
  return (
    <div className="flex flex-col h-screen overflow-hidden bg-background text-foreground">
      <SkillTreeHeader />

      <div className="flex flex-1 relative overflow-hidden">
        <SkillTreeCanvas />
        <ModuleSidebar />
      </div>
    </div>
  )
}
