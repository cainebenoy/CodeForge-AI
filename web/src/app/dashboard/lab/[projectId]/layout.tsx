/**
 * Lab layout — overrides dashboard layout to remove DashboardNavbar.
 * The Module Lab has its own dedicated LabHeader.
 */
export default function LabLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <>{children}</>
}
