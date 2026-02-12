/**
 * Curriculum layout — overrides dashboard layout to remove DashboardNavbar.
 * The Skill Tree page has its own dedicated header.
 */
export default function CurriculumLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <>{children}</>
}
