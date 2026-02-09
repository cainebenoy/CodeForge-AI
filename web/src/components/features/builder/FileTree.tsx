/**
 * Builder Mode - FileTree Component
 * Displays project file structure
 */

export function FileTree() {
  return (
    <div className="rounded-lg border bg-card p-4">
      <h3 className="mb-3 font-semibold">File Tree</h3>
      <div className="space-y-1 font-mono text-sm">
        <div>📁 src/</div>
        <div className="ml-4">📄 app/page.tsx</div>
      </div>
    </div>
  )
}
