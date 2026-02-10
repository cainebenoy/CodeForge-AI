'use client'

import {
  Bot,
  History,
  Send,
  Link2,
  Mic,
  MoreVertical,
  PlusCircle,
  Sparkles,
} from 'lucide-react'

/**
 * AgentChat — Right sidebar AI chat panel for Builder IDE.
 * Shows agent messages, user messages, a streaming indicator, and an input area.
 */
export function AgentChat() {
  return (
    <aside className="w-80 shrink-0 border-l border-border flex flex-col relative
                       dark:bg-secondary/80 dark:backdrop-blur-xl
                       glass-panel-light">
      {/* Gradient blob (dark mode) */}
      <div className="absolute top-0 right-0 -z-10 w-full h-64 bg-cf-primary/5 rounded-full blur-3xl opacity-20 pointer-events-none dark:block hidden" />

      {/* Header */}
      <div className="h-12 border-b border-border px-4 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Bot className="size-5 text-cf-primary" />
            <div className="absolute -top-0.5 -right-0.5 size-2.5 bg-cf-primary rounded-full border-2 border-background" />
          </div>
          <span className="font-semibold text-sm text-foreground">
            <span className="hidden dark:inline">Code Agent</span>
            <span className="inline dark:hidden">Builder Agent</span>
          </span>
          {/* Light-mode online dot */}
          <div className="size-2 rounded-full bg-emerald-600 shadow-[0_0_4px_rgba(5,148,103,0.4)] animate-pulse block dark:hidden" />
        </div>
        <div className="flex items-center gap-1">
          <button
            className="text-muted-foreground hover:text-foreground p-1 rounded hover:bg-muted"
            aria-label="Chat history"
          >
            <History className="size-4" />
          </button>
          <button
            className="text-muted-foreground hover:text-foreground p-1 rounded hover:bg-muted block dark:hidden"
            aria-label="More options"
          >
            <MoreVertical className="size-4" />
          </button>
        </div>
      </div>

      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-4 flex flex-col gap-4">
        {/* Agent message */}
        <div className="flex gap-3">
          <div className="size-8 shrink-0 rounded-full bg-cf-primary/10 flex items-center justify-center text-cf-primary">
            <Bot className="size-4" />
          </div>
          <div className="flex flex-col gap-1">
            <div className="text-xs text-muted-foreground">
              <span className="hidden dark:inline">Code Agent • 10:23 AM</span>
              <span className="inline dark:hidden font-semibold text-foreground">
                CodeForge AI
              </span>
            </div>
            <div className="p-3 bg-card dark:bg-muted/50 rounded-lg rounded-tl-none border border-border text-sm text-foreground/80 shadow-sm">
              <p>
                Hello! I&apos;m ready to help you build. I see you&apos;re
                working on the App.tsx file.
              </p>
              <p className="mt-2">
                Would you like me to scaffold a new component for the Data
                Visualization section?
              </p>
            </div>
          </div>
        </div>

        {/* User message */}
        <div className="flex gap-3 flex-row-reverse">
          <div className="size-8 shrink-0 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 border border-border" />
          <div className="flex flex-col gap-1 items-end">
            <div className="text-xs text-muted-foreground">
              <span className="hidden dark:inline">You • 10:24 AM</span>
              <span className="inline dark:hidden font-semibold text-foreground">
                You
              </span>
            </div>
            <div className="p-3 bg-cf-primary/20 dark:bg-cf-primary/20 rounded-lg rounded-tr-none border border-cf-primary/20 text-sm text-foreground shadow-sm">
              <p>
                Yes, please create a simple LineChart component using SVG.
              </p>
            </div>
          </div>
        </div>

        {/* Agent streaming message */}
        <div className="flex gap-3">
          <div className="size-8 shrink-0 rounded-full bg-cf-primary/10 flex items-center justify-center text-cf-primary">
            <Bot className="size-4" />
          </div>
          <div className="flex flex-col gap-1 w-full min-w-0">
            <div className="text-xs text-muted-foreground flex items-center gap-2">
              <span className="hidden dark:inline">Code Agent</span>
              <span className="inline dark:hidden font-semibold text-foreground">
                CodeForge AI
              </span>
              <span className="flex gap-0.5">
                <span className="size-1 bg-cf-primary rounded-full animate-bounce" />
                <span className="size-1 bg-cf-primary rounded-full animate-bounce [animation-delay:75ms]" />
                <span className="size-1 bg-cf-primary rounded-full animate-bounce [animation-delay:150ms]" />
              </span>
            </div>
            <div className="p-3 bg-card dark:bg-muted/50 rounded-lg rounded-tl-none border border-border text-sm text-foreground/80 shadow-sm w-full">
              <p className="mb-2">
                Sure! Here is a starting point for your{' '}
                <code className="font-mono bg-muted px-1 rounded text-xs">
                  LineChart.tsx
                </code>
                :
              </p>

              {/* Code snippet */}
              <div className="bg-muted dark:bg-black rounded-md p-2 border border-border font-mono text-xs overflow-x-auto">
                <div className="flex justify-between items-center mb-1 pb-1 border-b border-border">
                  <span className="text-muted-foreground text-[10px]">
                    TypeScript
                  </span>
                  <span className="text-[10px] text-muted-foreground cursor-pointer hover:text-foreground">
                    Copy
                  </span>
                </div>
                <span className="syn-keyword">const</span>{' '}
                <span className="syn-function">LineChart</span>
                {' = ({ '}
                <span className="syn-variable">data</span>
                {' }) => {\n'}
                {'  '}
                <span className="syn-keyword">return</span> (
                {'\n'}
                {'    <'}
                <span className="syn-tag">svg</span>{' '}
                <span className="syn-attr">viewBox</span>=
                <span className="syn-string">&quot;0 0 100 50&quot;</span>
                {'>\n'}
                {'      '}
                <span className="syn-comment">
                  {'/* ...implementation... */'}
                </span>
                {'\n'}
                {'    </'}
                <span className="syn-tag">svg</span>
                {'>\n'}
                {'  );\n'}
                {'};'}
              </div>

              {/* Action buttons (light mode) */}
              <div className="mt-3 flex gap-2 dark:hidden">
                <button className="text-xs border border-border bg-muted hover:bg-background hover:border-cf-primary text-muted-foreground px-3 py-1.5 rounded transition-all">
                  Insert Code
                </button>
                <button className="text-xs border border-border bg-muted hover:bg-background hover:border-cf-primary text-muted-foreground px-3 py-1.5 rounded transition-all">
                  Explain
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-border bg-background/50 dark:bg-background shrink-0 backdrop-blur-sm">
        <div className="relative">
          <textarea
            className="w-full bg-card dark:bg-secondary text-foreground text-sm rounded-lg border border-border p-3 pr-10 focus:ring-1 focus:ring-cf-primary focus:border-cf-primary outline-none resize-none h-20 placeholder:text-muted-foreground custom-scrollbar shadow-inner"
            placeholder="Ask anything about your code..."
          />
          {/* Dark-mode bottom-left icons */}
          <div className="absolute bottom-3 left-3 flex gap-2 dark:flex hidden">
            <button
              className="text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Attach code context"
            >
              <Link2 className="size-4" />
            </button>
            <button
              className="text-muted-foreground hover:text-foreground transition-colors"
              aria-label="Voice input"
            >
              <Mic className="size-4" />
            </button>
          </div>
          {/* Send / Attach for light mode */}
          <div className="absolute right-2 bottom-2 flex items-center gap-1">
            <button
              className="p-1.5 text-muted-foreground hover:text-cf-primary hover:bg-muted rounded-full transition-colors block dark:hidden"
              aria-label="Attach context"
            >
              <PlusCircle className="size-4" />
            </button>
            <button
              className="p-1.5 bg-cf-primary text-black rounded-md hover:brightness-110 transition-colors shadow-sm"
              aria-label="Send message"
            >
              <Send className="size-4" />
            </button>
          </div>
        </div>
        {/* Footer hint */}
        <div className="flex items-center justify-between mt-2 px-1">
          <span className="text-[10px] text-muted-foreground hidden dark:inline">
            Press Enter to send, Shift+Enter for new line
          </span>
          <span className="text-[10px] text-cf-primary/80 font-medium hidden dark:inline">
            GPT-4 Turbo
          </span>
          {/* Light-mode disclaimer */}
          <span className="text-[10px] text-muted-foreground flex items-center gap-1 dark:hidden mx-auto">
            <Sparkles className="size-2.5" />
            AI generated content may be inaccurate.
          </span>
        </div>
      </div>
    </aside>
  )
}
