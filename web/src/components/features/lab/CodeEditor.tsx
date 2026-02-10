'use client'

import { useState } from 'react'
import { FileJson, FileCode2, FileText, Code, FlaskConical, Trash2, ChevronDown, X } from 'lucide-react'

/* ─── Dark-mode tabs ─── */
const darkTabs = [
  { name: 'schema.sql', icon: <FileJson className="size-4 text-orange-400" />, active: true },
  { name: 'index.ts', icon: <FileCode2 className="size-4 text-blue-400" />, active: false },
  { name: 'README.md', icon: <FileText className="size-4 text-yellow-400" />, active: false },
]

/* ─── Light-mode tabs ─── */
const lightTabs = [
  { name: 'solution.py', icon: <Code className="size-[14px] text-yellow-600" />, active: true },
  { name: 'tests.py', icon: <FlaskConical className="size-[14px] text-blue-600" />, active: false },
]

/* ─── Dark SQL lines (One Dark–style tokens) ─── */
const darkLines = [
  '<span class="syn-comment">-- Task: Improve search performance for user emails</span>',
  '<span class="syn-comment">-- Current status: Full Table Scan (Slow)</span>',
  '',
  '<span class="syn-keyword">CREATE TABLE</span> <span class="syn-variable">users</span> (',
  '  <span class="syn-variable">id</span> <span class="syn-keyword">SERIAL PRIMARY KEY</span>,',
  '  <span class="syn-variable">email</span> <span class="syn-keyword">VARCHAR</span>(<span class="syn-number">255</span>) <span class="syn-keyword">NOT NULL</span>,',
  '  <span class="syn-variable">created_at</span> <span class="syn-keyword">TIMESTAMP DEFAULT NOW</span>()',
  ');',
  '',
  '<span class="syn-comment">-- TODO: Write your solution below</span>',
  '<span class="syn-comment">-- Hint: Use B-Tree for range and equality</span>',
  '',
  '<span class="syn-keyword">CREATE INDEX</span> <span class="syn-variable">idx_users_email</span>',
  '<span class="syn-keyword">ON</span> <span class="syn-variable">users</span> (<span class="syn-variable">email</span>);',
  '',
  '<span class="syn-keyword">EXPLAIN ANALYZE SELECT</span> * <span class="syn-keyword">FROM</span> <span class="syn-variable">users</span> <span class="syn-keyword">WHERE</span> <span class="syn-variable">email</span> = <span class="syn-string">\'student@codeforge.ai\'</span>;',
]

/* ─── Light Python lines (GitHub Light–style tokens) ─── */
const lightLines = [
  '<span class="syn-keyword">def</span> <span class="syn-function">fibonacci</span>(n):',
  '    <span class="syn-comment"># Check for negative input</span>',
  '    <span class="syn-keyword">if</span> n &lt; <span class="syn-number">0</span>:',
  '        <span class="syn-keyword">print</span>(<span class="syn-string">"Incorrect input"</span>)',
  '',
  '    <span class="syn-comment"># Base cases</span>',
  '    <span class="syn-keyword">elif</span> n == <span class="syn-number">0</span>:',
  '        <span class="syn-keyword">return</span> <span class="syn-number">0</span>',
  '    <span class="syn-keyword">elif</span> n == <span class="syn-number">1</span>:',
  '        <span class="syn-keyword">return</span> <span class="syn-number">1</span>',
  '',
  '    <span class="syn-keyword">else</span>:',
  '        <span class="syn-comment"># TODO: Implement recursive or iterative logic here</span>',
  '        <span class="syn-keyword">return</span> fibonacci(n-<span class="syn-number">1</span>) + fibonacci(n-<span class="syn-number">2</span>)',
  '',
  '    <span class="syn-keyword">pass</span>',
]

/**
 * CodeEditor — Central editor pane for the Module Lab.
 *
 * **Dark**: Zinc-950 editor with One Dark syntax, SQL code, mini terminal.
 * **Light**: White editor with GitHub Light syntax, Python code, console output.
 *
 * Uses `dangerouslySetInnerHTML` for the static demo syntax tokens.
 */
export function CodeEditor() {
  const [darkActive, setDarkActive] = useState(0)
  const [lightActive, setLightActive] = useState(0)

  return (
    <>
      {/* ═══ DARK ═══ */}
      <section className="hidden dark:flex flex-1 flex-col bg-black relative min-w-0">
        {/* Tabs */}
        <div className="flex items-center bg-zinc-950 border-b border-zinc-800">
          {darkTabs.map((tab, i) => (
            <button
              key={tab.name}
              onClick={() => setDarkActive(i)}
              className={`px-4 py-2.5 text-xs font-mono flex items-center gap-2 transition-colors border-t-2 ${
                i === darkActive
                  ? 'border-violet-500 bg-zinc-950 text-foreground'
                  : 'border-transparent text-zinc-500 hover:text-zinc-300 hover:bg-zinc-900/50'
              }`}
            >
              {tab.icon}
              {tab.name}
            </button>
          ))}
        </div>

        {/* Editor surface */}
        <div className="flex-1 flex overflow-hidden font-mono text-sm leading-6">
          {/* Line numbers */}
          <div className="w-12 bg-zinc-950 text-zinc-600 flex flex-col items-end pr-3 pt-4 select-none border-r border-zinc-800 shrink-0 text-xs">
            {darkLines.map((_, i) => (
              <div key={i}>{i + 1}</div>
            ))}
          </div>
          {/* Code */}
          <div className="flex-1 p-4 overflow-auto text-zinc-300">
            {darkLines.map((line, i) => (
              <div
                key={i}
                className="whitespace-pre"
                dangerouslySetInnerHTML={{ __html: line || ' ' }}
              />
            ))}
          </div>
        </div>

        {/* Terminal */}
        <div className="h-32 bg-zinc-950 border-t border-zinc-800 flex flex-col shrink-0">
          <div className="flex items-center justify-between px-4 py-1.5 border-b border-zinc-800 bg-zinc-900/30">
            <span className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
              Terminal
            </span>
            <div className="flex gap-2">
              <button className="text-zinc-500 hover:text-zinc-300" aria-label="Clear">
                <Trash2 className="size-4" />
              </button>
              <button className="text-zinc-500 hover:text-zinc-300" aria-label="Collapse">
                <ChevronDown className="size-4" />
              </button>
            </div>
          </div>
          <div className="p-3 font-mono text-xs text-muted-foreground overflow-y-auto custom-scrollbar">
            <div className="flex gap-2">
              <span className="text-emerald-500">➜</span>
              <span>postgres running on port 5432...</span>
            </div>
            <div className="flex gap-2 mt-1">
              <span className="text-emerald-500">➜</span>
              <span>Waiting for query execution...</span>
            </div>
          </div>
        </div>
      </section>

      {/* ═══ LIGHT ═══ */}
      <section className="flex dark:hidden flex-1 flex-col bg-white relative min-w-0">
        {/* Tabs */}
        <div className="flex h-10 border-b border-border bg-muted/40 items-end px-2 gap-1">
          {lightTabs.map((tab, i) => (
            <button
              key={tab.name}
              onClick={() => setLightActive(i)}
              className={`flex items-center gap-2 px-4 py-2 text-xs font-medium transition-colors ${
                i === lightActive
                  ? 'bg-white border-t border-l border-r border-border rounded-t-sm text-foreground relative top-[1px] border-t-2 border-t-blue-600'
                  : 'border border-transparent rounded-t-sm text-muted-foreground hover:bg-muted mb-[1px]'
              }`}
            >
              {tab.icon}
              {tab.name}
              {i === lightActive && (
                <span className="hover:bg-muted rounded p-0.5 ml-2">
                  <X className="size-3 text-muted-foreground" />
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Editor */}
        <div className="flex-1 relative flex overflow-hidden">
          {/* Line numbers */}
          <div className="w-12 bg-white border-r border-muted flex flex-col items-end py-4 pr-3 select-none text-right">
            {lightLines.map((_, i) => (
              <span key={i} className="text-xs font-mono text-muted-foreground/40 leading-6">
                {i + 1}
              </span>
            ))}
          </div>
          {/* Code */}
          <div className="flex-1 p-4 overflow-auto font-mono text-sm leading-6">
            <pre className="m-0">
              <code>
                {lightLines.map((line, i) => (
                  <div
                    key={i}
                    className="whitespace-pre"
                    dangerouslySetInnerHTML={{ __html: line || ' ' }}
                  />
                ))}
              </code>
            </pre>
          </div>
        </div>

        {/* Console */}
        <div className="h-48 border-t border-border bg-muted/20 flex flex-col">
          <div className="flex items-center justify-between px-4 py-2 border-b border-muted bg-muted/30">
            <span className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
              Console Output
            </span>
            <div className="flex gap-2">
              <button className="p-1 hover:bg-muted rounded" aria-label="Clear">
                <Trash2 className="size-4 text-muted-foreground" />
              </button>
              <button className="p-1 hover:bg-muted rounded" aria-label="Collapse">
                <ChevronDown className="size-4 text-muted-foreground" />
              </button>
            </div>
          </div>
          <div className="p-4 font-mono text-xs overflow-y-auto">
            <div className="flex gap-2 mb-1">
              <span className="text-muted-foreground select-none">$</span>
              <span className="text-foreground">python solution.py</span>
            </div>
            <div className="flex gap-2 mb-1">
              <span className="text-emerald-600 select-none">➜</span>
              <span className="text-muted-foreground">Running basic tests...</span>
            </div>
            <div className="flex gap-2 mb-1">
              <span className="text-red-500 select-none">✖</span>
              <span className="text-red-600">
                RecursionError: maximum recursion depth exceeded while calling a Python object
              </span>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
