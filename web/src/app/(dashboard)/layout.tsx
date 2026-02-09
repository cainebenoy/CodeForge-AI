export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar placeholder */}
      <aside className="w-64 border-r bg-muted/40 p-4">
        <div className="mb-4 text-lg font-bold">CodeForge AI</div>
        <nav className="space-y-2">
          <div className="rounded-md px-3 py-2 text-sm hover:bg-muted">
            Dashboard
          </div>
          <div className="rounded-md px-3 py-2 text-sm hover:bg-muted">
            Builder Mode
          </div>
          <div className="rounded-md px-3 py-2 text-sm hover:bg-muted">
            Student Mode
          </div>
        </nav>
      </aside>

      {/* Main content */}
      <div className="flex-1">
        <header className="border-b bg-background px-6 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold">Dashboard</h2>
            <div className="text-sm text-muted-foreground">User Menu</div>
          </div>
        </header>
        <main className="p-6">{children}</main>
      </div>
    </div>
  )
}
