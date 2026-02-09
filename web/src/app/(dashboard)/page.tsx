export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
        <p className="text-muted-foreground">
          Manage your Builder and Student mode projects
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <div className="rounded-lg border bg-card p-6 shadow-sm">
          <h3 className="mb-2 font-semibold">Create New Project</h3>
          <p className="text-sm text-muted-foreground">
            Start a new Builder Mode project
          </p>
        </div>
      </div>
    </div>
  )
}
