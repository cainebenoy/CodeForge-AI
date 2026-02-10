/**
 * HeroTerminal — Dark-mode terminal hero visual
 * Only visible in dark mode.
 */
export function HeroTerminal() {
  return (
    <div className="hidden dark:block w-full max-w-3xl mx-auto mt-6">
      <div className="glass-panel rounded-xl overflow-hidden shadow-2xl shadow-black/80 transition-all duration-500 hover:shadow-cf-primary/5 hover:border-white/15">
        {/* Terminal Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-white/5 border-b border-white/5">
          <div className="flex items-center gap-2">
            <div className="size-3 rounded-full bg-[#ff5f56]" />
            <div className="size-3 rounded-full bg-[#ffbd2e]" />
            <div className="size-3 rounded-full bg-[#27c93f]" />
          </div>
          <div className="text-xs font-mono text-gray-500 flex items-center gap-2 opacity-60">
            <svg className="size-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            cf-agent-1 — zsh — 80×24
          </div>
          <div className="w-4" />
        </div>

        {/* Terminal Body */}
        <div className="p-6 font-mono text-sm md:text-base leading-relaxed h-[340px] overflow-y-auto custom-scrollbar flex flex-col justify-end bg-black/40 relative">
          {/* Glow */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-64 h-64 bg-cf-primary/5 blur-[100px] rounded-full pointer-events-none" />

          <div className="flex flex-col gap-2 relative z-10">
            <div className="text-gray-500 mb-2">
              Last login: Today at 09:41:23 on ttys001
            </div>
            <div className="flex items-center gap-2 text-gray-400">
              <span className="text-emerald-500">➜</span>
              <span>initializing codeforge_env...</span>
            </div>
            <div className="pl-6 text-xs text-gray-500">
              Loading modules: [architect, research, deploy]... OK
            </div>

            {/* Command 1 */}
            <div className="mt-3 flex gap-2 text-white">
              <span className="font-bold text-emerald-500">➜</span>
              <span className="text-blue-300">~</span>
              <span>architect-agent --scan ./src</span>
            </div>
            <div className="ml-5 border-l border-gray-700 pl-4 py-1 text-xs sm:text-sm text-gray-400">
              Scanning project structure...<br />
              Found 24 modules.<br />
              Dependency graph built.
            </div>

            {/* Command 2 */}
            <div className="mt-3 flex gap-2 text-white">
              <span className="font-bold text-emerald-500">➜</span>
              <span className="text-blue-300">~</span>
              <span>research-agent --analyze &quot;Scale DB sharding&quot;</span>
            </div>
            <div className="ml-5 border-l border-gray-700 pl-4 py-1 flex flex-col gap-1 text-xs sm:text-sm">
              <span className="text-gray-400">Retrieving technical context...</span>
              <span className="text-gray-300">
                Analyzing requirements...{' '}
                <span className="font-bold text-cf-primary drop-shadow-[0_0_8px_rgba(19,236,109,0.5)]">
                  [Success]
                </span>
              </span>
            </div>

            {/* Active Prompt */}
            <div className="mt-3 flex items-center gap-2 text-white">
              <span className="font-bold text-emerald-500">➜</span>
              <span className="text-blue-300">~</span>
              <span className="font-bold">_</span>
              <span className="cursor-blink w-2.5 h-5 bg-cf-primary block shadow-[0_0_8px_rgba(19,236,109,0.8)]" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
