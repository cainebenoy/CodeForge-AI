/**
 * Builder layout — overrides the dashboard layout to remove DashboardNavbar.
 * The Builder IDE is a full-screen experience with its own header.
 */
export default function BuilderLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <>{children}</>
}
