/**
 * Student layout — overrides dashboard layout to remove DashboardNavbar.
 * The Student Choice page is a full-screen modal experience.
 */
export default function StudentLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <>{children}</>
}
