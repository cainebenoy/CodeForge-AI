'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import {
  Bot,
  History,
  Send,
  Link2,
  Mic,
  MoreVertical,
  PlusCircle,
  Sparkles,
  Loader2,
} from 'lucide-react'
import { useRunAgent, useJobStream } from '@/lib/hooks/use-agents'
import { useBuilderStore } from '@/store/useBuilderStore'
import type { AgentType } from '@/types/api.types'

interface ChatMessage {
  id: string
  role: 'user' | 'agent'
  content: string
  timestamp: Date
}

/**
 * AgentChat — Right sidebar AI chat panel for Builder IDE.
 *
 * Sends agent requests via use-agents hooks and streams responses
 * via SSE. Maintains a local chat history per session.
 */
export function AgentChat({ projectId }: { projectId: string }) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      role: 'agent',
      content:
        "Hello! I'm ready to help you build. What would you like me to work on?",
      timestamp: new Date(),
    },
  ])
  const [input, setInput] = useState('')
  const [activeJobId, setActiveJobId] = useState<string | null>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const activeAgent = useBuilderStore((s) => s.activeAgent)

  const runAgent = useRunAgent()
  const { latestEvent, isConnected } = useJobStream(activeJobId)

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, latestEvent])

  // Handle SSE events → append agent messages
  useEffect(() => {
    if (!latestEvent) return

    if (latestEvent.status === 'completed' && 'result' in latestEvent) {
      const result = latestEvent.result
      const summary =
        typeof result === 'object' && result && 'summary' in result
          ? String((result as Record<string, unknown>).summary)
          : 'Task completed successfully.'

      setMessages((prev) => [
        ...prev,
        {
          id: `agent-${Date.now()}`,
          role: 'agent',
          content: summary,
          timestamp: new Date(),
        },
      ])
      setActiveJobId(null)
    } else if (latestEvent.status === 'failed' && 'error' in latestEvent) {
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: 'agent',
          content: `Error: ${latestEvent.error}`,
          timestamp: new Date(),
        },
      ])
      setActiveJobId(null)
    }
  }, [latestEvent])

  const handleSend = useCallback(async () => {
    const trimmed = input.trim()
    if (!trimmed || runAgent.isPending) return

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: trimmed,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMsg])
    setInput('')

    try {
      const agentType: AgentType = activeAgent ?? 'code'
      const response = await runAgent.mutateAsync({
        project_id: projectId,
        agent_type: agentType,
        input_context: { user_message: trimmed },
      })
      setActiveJobId(response.job_id)
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: `error-${Date.now()}`,
          role: 'agent',
          content: 'Failed to reach the agent. Please try again.',
          timestamp: new Date(),
        },
      ])
    }
  }, [input, projectId, activeAgent, runAgent])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const isProcessing = runAgent.isPending || isConnected

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
            <div className={`absolute -top-0.5 -right-0.5 size-2.5 rounded-full border-2 border-background ${
              isProcessing ? 'bg-amber-400 animate-pulse' : 'bg-cf-primary'
            }`} />
          </div>
          <span className="font-semibold text-sm text-foreground">
            <span className="hidden dark:inline">
              {activeAgent ? `${activeAgent.charAt(0).toUpperCase() + activeAgent.slice(1)} Agent` : 'Code Agent'}
            </span>
            <span className="inline dark:hidden">Builder Agent</span>
          </span>
          {!isProcessing && (
            <div className="size-2 rounded-full bg-emerald-600 shadow-[0_0_4px_rgba(5,148,103,0.4)] animate-pulse block dark:hidden" />
          )}
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
        {messages.map((msg) =>
          msg.role === 'agent' ? (
            <div key={msg.id} className="flex gap-3">
              <div className="size-8 shrink-0 rounded-full bg-cf-primary/10 flex items-center justify-center text-cf-primary">
                <Bot className="size-4" />
              </div>
              <div className="flex flex-col gap-1">
                <div className="text-xs text-muted-foreground">
                  <span className="hidden dark:inline">Code Agent</span>
                  <span className="inline dark:hidden font-semibold text-foreground">
                    CodeForge AI
                  </span>
                </div>
                <div className="p-3 bg-card dark:bg-muted/50 rounded-lg rounded-tl-none border border-border text-sm text-foreground/80 shadow-sm whitespace-pre-wrap">
                  {msg.content}
                </div>
              </div>
            </div>
          ) : (
            <div key={msg.id} className="flex gap-3 flex-row-reverse">
              <div className="size-8 shrink-0 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 border border-border" />
              <div className="flex flex-col gap-1 items-end">
                <div className="text-xs text-muted-foreground">You</div>
                <div className="p-3 bg-cf-primary/20 dark:bg-cf-primary/20 rounded-lg rounded-tr-none border border-cf-primary/20 text-sm text-foreground shadow-sm">
                  {msg.content}
                </div>
              </div>
            </div>
          ),
        )}

        {/* Streaming indicator */}
        {isProcessing && (
          <div className="flex gap-3">
            <div className="size-8 shrink-0 rounded-full bg-cf-primary/10 flex items-center justify-center text-cf-primary">
              <Bot className="size-4" />
            </div>
            <div className="flex flex-col gap-1">
              <div className="text-xs text-muted-foreground flex items-center gap-2">
                <span>Working</span>
                <span className="flex gap-0.5">
                  <span className="size-1 bg-cf-primary rounded-full animate-bounce" />
                  <span className="size-1 bg-cf-primary rounded-full animate-bounce [animation-delay:75ms]" />
                  <span className="size-1 bg-cf-primary rounded-full animate-bounce [animation-delay:150ms]" />
                </span>
              </div>
              {latestEvent && 'progress' in latestEvent && (
                <div className="w-full bg-muted rounded-full h-1.5 mt-1">
                  <div
                    className="bg-cf-primary h-1.5 rounded-full transition-all duration-500"
                    style={{ width: `${latestEvent.progress}%` }}
                  />
                </div>
              )}
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-border bg-background/50 dark:bg-background shrink-0 backdrop-blur-sm">
        <div className="relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isProcessing}
            className="w-full bg-card dark:bg-secondary text-foreground text-sm rounded-lg border border-border p-3 pr-10 focus:ring-1 focus:ring-cf-primary focus:border-cf-primary outline-none resize-none h-20 placeholder:text-muted-foreground custom-scrollbar shadow-inner disabled:opacity-50"
            placeholder={isProcessing ? 'Agent is working...' : 'Ask anything about your code...'}
          />
          {/* Dark-mode bottom-left icons */}
          <div className="absolute bottom-3 left-3 gap-2 hidden dark:flex">
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
              onClick={handleSend}
              disabled={isProcessing || !input.trim()}
              className="p-1.5 bg-cf-primary text-black rounded-md hover:brightness-110 transition-colors shadow-sm disabled:opacity-50"
              aria-label="Send message"
            >
              {isProcessing ? (
                <Loader2 className="size-4 animate-spin" />
              ) : (
                <Send className="size-4" />
              )}
            </button>
          </div>
        </div>
        {/* Footer hint */}
        <div className="flex items-center justify-between mt-2 px-1">
          <span className="text-[10px] text-muted-foreground hidden dark:inline">
            Press Enter to send, Shift+Enter for new line
          </span>
          <span className="text-[10px] text-cf-primary/80 font-medium hidden dark:inline">
            {activeAgent ?? 'code'} agent
          </span>
          <span className="text-[10px] text-muted-foreground flex items-center gap-1 dark:hidden mx-auto">
            <Sparkles className="size-2.5" />
            AI generated content may be inaccurate.
          </span>
        </div>
      </div>
    </aside>
  )
}
