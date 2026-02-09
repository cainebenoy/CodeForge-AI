export default function StudentProjectPage({
  params,
}: {
  params: { projectId: string }
}) {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">
        Student Project: {params.projectId}
      </h1>
      <div className="rounded-lg border bg-card p-6">
        <p className="text-muted-foreground">
          Student Mode interface will be implemented here.
        </p>
      </div>
    </div>
  )
}
