import { Plus } from 'lucide-react'

/**
 * CreateProjectCard — dashed empty-state card that opens project creation.
 * Works as a button; the parent handles the click/modal.
 */
export function CreateProjectCard({
  onClick,
}: {
  onClick?: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="group flex flex-col items-center justify-center min-h-[240px] rounded-lg border-2 border-dashed border-border hover:border-cf-primary dark:hover:border-cf-primary/50 bg-transparent hover:bg-cf-primary/5 transition-all duration-300 cursor-pointer"
    >
      <div className="w-14 h-14 rounded-full bg-muted border border-border flex items-center justify-center mb-4 group-hover:text-cf-primary group-hover:border-cf-primary transition-colors">
        <Plus className="size-7 text-muted-foreground group-hover:text-cf-primary transition-colors" />
      </div>
      <h3 className="text-base font-bold text-foreground">Create New Project</h3>
      <p className="text-xs text-muted-foreground mt-1 text-center max-w-[200px]">
        Start from scratch or import an existing repository.
      </p>
    </button>
  )
}
