/**
 * HeroCodeBlock — Light-mode code-block hero visual
 * Only visible in light mode.
 */
export function HeroCodeBlock() {
  return (
    <div className="block dark:hidden w-full flex-1 lg:min-w-[500px] relative group">
      {/* Decorative blur */}
      <div className="absolute -inset-4 bg-gradient-to-r from-gray-100 to-gray-50 rounded-lg opacity-50 blur-2xl -z-10" />

      <div className="bg-white rounded-md border border-gray-200 overflow-hidden flex flex-col lab-shadow transition-transform duration-500 hover:-translate-y-1">
        {/* Title Bar */}
        <div className="bg-white border-b border-gray-100 px-4 py-3 flex items-center justify-between">
          <div className="flex gap-2">
            <div className="w-3 h-3 rounded-full border border-gray-300 bg-transparent" />
            <div className="w-3 h-3 rounded-full border border-gray-300 bg-transparent" />
            <div className="w-3 h-3 rounded-full border border-gray-300 bg-transparent" />
          </div>
          <div className="text-xs font-mono text-gray-400 flex items-center gap-1">
            <svg className="size-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            architecture.tf
          </div>
          <div className="w-10" />
        </div>

        {/* Code Content */}
        <div className="p-6 overflow-x-auto bg-white">
          <pre className="text-sm leading-relaxed text-[#24292e]">
            <code>
              <span className="code-syntax-keyword">resource</span>{' '}
              <span className="code-syntax-string">&quot;aws_ecs_cluster&quot;</span>{' '}
              <span className="code-syntax-string">&quot;main&quot;</span>
              {' {\n'}
              {'  '}
              <span className="code-syntax-constant">name</span>
              {' = '}
              <span className="code-syntax-string">&quot;production-cluster&quot;</span>
              {'\n\n'}
              {'  '}
              <span className="code-syntax-keyword">setting</span>
              {' {\n'}
              {'    '}
              <span className="code-syntax-constant">name</span>
              {'  = '}
              <span className="code-syntax-string">&quot;containerInsights&quot;</span>
              {'\n'}
              {'    '}
              <span className="code-syntax-constant">value</span>
              {' = '}
              <span className="code-syntax-string">&quot;enabled&quot;</span>
              {'\n  }\n}\n\n'}
              <span className="code-syntax-comment">{'# CodeForge: Auto-generated scaling logic'}</span>
              {'\n'}
              <span className="code-syntax-keyword">module</span>{' '}
              <span className="code-syntax-string">&quot;autoscaling&quot;</span>
              {' {\n'}
              {'  '}
              <span className="code-syntax-constant">source</span>
              {' = '}
              <span className="code-syntax-string">&quot;./modules/scaling&quot;</span>
              {'\n\n'}
              {'  '}
              <span className="code-syntax-constant">min_capacity</span>
              {' = '}
              <span className="code-syntax-constant">2</span>
              {'\n'}
              {'  '}
              <span className="code-syntax-constant">max_capacity</span>
              {' = '}
              <span className="code-syntax-constant">10</span>
              {'\n'}
              {'  '}
              <span className="code-syntax-constant">cpu_target</span>
              {'   = '}
              <span className="code-syntax-constant">75</span>
              {'\n}\n\n'}
              <span className="code-syntax-keyword">output</span>{' '}
              <span className="code-syntax-string">&quot;cluster_id&quot;</span>
              {' {\n'}
              {'  '}
              <span className="code-syntax-constant">value</span>
              {' = '}
              <span className="code-syntax-function">aws_ecs_cluster</span>
              {'.main.id\n}'}
            </code>
          </pre>
        </div>

        {/* Status Bar */}
        <div className="bg-gray-50 border-t border-gray-100 px-4 py-1.5 flex justify-between items-center text-[10px] font-mono text-gray-500">
          <div className="flex items-center gap-3">
            <span>master*</span>
            <span className="flex items-center gap-1">
              <svg className="size-2.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Validated
            </span>
          </div>
          <div>Ln 24, Col 2</div>
        </div>
      </div>
    </div>
  )
}
