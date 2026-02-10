/**
 * Project status layout — overrides dashboard layout.
 * Dark mode renders its own header; light mode is a centred standalone accordion.
 */
export default function ProjectLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return <>{children}</>
}
