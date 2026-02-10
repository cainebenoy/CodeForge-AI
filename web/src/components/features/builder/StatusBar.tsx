import {
  GitBranch,
  RefreshCw,
  AlertCircle,
  AlertTriangle,
  Bell,
  FileCode,
} from 'lucide-react'

/**
 * StatusBar — Bottom bar for the Builder IDE.
 * Dark mode: green accent bar.
 * Light mode: neutral gray bar.
 */
export function StatusBar() {
  return (
    <footer className="h-6 shrink-0 z-20 flex items-center justify-between px-3 text-xs font-mono font-medium select-none
                        dark:bg-cf-primary dark:text-black
                        bg-[#f0f0f0] border-t border-border text-muted-foreground">
      {/* Left */}
      <div className="flex items-center gap-4 h-full">
        <div className="flex items-center gap-1 hover:bg-black/10 dark:hover:bg-black/10 hover:bg-muted px-1.5 rounded cursor-pointer h-5 transition-colors">
          <GitBranch className="size-3" />
          <span className="dark:text-black text-foreground font-medium">main*</span>
        </div>
        <div className="flex items-center gap-1 hover:bg-black/10 dark:hover:bg-black/10 hover:bg-muted px-1.5 rounded cursor-pointer h-5 transition-colors">
          <RefreshCw className="size-3" />
        </div>
        <div className="flex items-center gap-1 hover:bg-black/10 dark:hover:bg-black/10 hover:bg-muted px-1.5 rounded cursor-pointer h-5 transition-colors">
          <AlertCircle className="size-3" />
          <span>0</span>
          <AlertTriangle className="size-3 ml-1" />
          <span>0</span>
        </div>
      </div>

      {/* Right */}
      <div className="flex items-center gap-4 h-full">
        <span className="hover:bg-black/10 dark:hover:bg-black/10 hover:bg-muted px-1.5 rounded cursor-pointer h-5 flex items-center transition-colors">
          Ln 12, Col 47
        </span>
        <span className="hover:bg-black/10 dark:hover:bg-black/10 hover:bg-muted px-1.5 rounded cursor-pointer h-5 flex items-center transition-colors">
          Spaces: 2
        </span>
        <span className="hover:bg-black/10 dark:hover:bg-black/10 hover:bg-muted px-1.5 rounded cursor-pointer h-5 flex items-center transition-colors">
          UTF-8
        </span>
        <div className="flex items-center gap-1 hover:bg-black/10 dark:hover:bg-black/10 hover:bg-muted px-1.5 rounded cursor-pointer h-5 transition-colors dark:text-blue-900 text-cf-primary font-medium">
          <FileCode className="size-3" />
          <span>TypeScript JSX</span>
        </div>
        <div className="hover:bg-black/10 dark:hover:bg-black/10 hover:bg-muted px-1.5 rounded cursor-pointer h-5 flex items-center transition-colors">
          <Bell className="size-3" />
        </div>
      </div>
    </footer>
  )
}
