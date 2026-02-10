/**
 * TerminalPanel — Integrated terminal drawer (light mode only, hidden in dark mode).
 * Shows a simulated Vite dev server output.
 */
export function TerminalPanel() {
  return (
    <div className="h-40 border-t border-border bg-background flex flex-col dark:hidden">
      {/* Tab bar */}
      <div className="flex items-center px-4 py-1 gap-6 border-b border-border/50 bg-muted/30">
        <button className="text-xs font-semibold text-foreground border-b-2 border-cf-primary pb-1 pt-1">
          TERMINAL
        </button>
        <button className="text-xs font-medium text-muted-foreground hover:text-foreground pb-1 pt-1">
          OUTPUT
        </button>
        <button className="text-xs font-medium text-muted-foreground hover:text-foreground pb-1 pt-1">
          DEBUG CONSOLE
        </button>
        <button className="text-xs font-medium text-muted-foreground hover:text-foreground pb-1 pt-1">
          PROBLEMS{' '}
          <span className="bg-muted text-muted-foreground rounded-full px-1.5 py-0.5 text-[10px] ml-1">
            0
          </span>
        </button>
      </div>

      {/* Terminal content */}
      <div className="flex-1 p-3 font-mono text-xs overflow-y-auto">
        <div className="text-muted-foreground mb-2">
          Microsoft Windows [Version 10.0.19045.3693]
        </div>
        <div className="flex items-center gap-2">
          <span className="text-emerald-600 font-bold">➜</span>
          <span className="text-cyan-600 font-bold">project-alpha</span>
          <span className="text-muted-foreground">
            git:(<span className="text-red-500 font-bold">main</span>)
          </span>
          <span className="text-foreground">npm run dev</span>
        </div>
        <div className="mt-2 text-muted-foreground">
          &gt; project-alpha@0.0.1 dev
          <br />
          &gt; vite
        </div>
        <div className="mt-2 text-emerald-600 font-bold">
          VITE v5.0.0{' '}
          <span className="text-muted-foreground font-normal">
            ready in 245 ms
          </span>
        </div>
        <div className="mt-2 flex flex-col gap-1 text-foreground/80">
          <div className="flex items-center gap-2">
            <span className="font-bold text-emerald-600">➜</span>
            <span className="font-bold">Local:</span>
            <span className="text-blue-500 underline cursor-pointer">
              http://localhost:5173/
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-emerald-600">➜</span>
            <span className="font-bold">Network:</span>
            <span className="text-muted-foreground">
              use --host to expose
            </span>
          </div>
        </div>
        <div className="mt-2 flex items-center gap-2">
          <span className="text-emerald-600 font-bold">➜</span>
          <span className="text-cyan-600 font-bold">project-alpha</span>
          <span className="text-muted-foreground">
            git:(<span className="text-red-500 font-bold">main</span>)
          </span>
          <span className="inline-block w-2 h-4 bg-muted-foreground align-middle animate-pulse" />
        </div>
      </div>
    </div>
  )
}
