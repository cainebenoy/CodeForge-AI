'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
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
import {
  useRunAgent,
  useProjectChat,
  chatKeys,
} from '@/lib/hooks/use-agents'
import { useRealtimeSubscription } from '@/lib/hooks/use-realtime'
import { useBuilderStore } from '@/store/useBuilderStore'
import type { AgentType, ChatMessage } from '@/types/api.types'
import { useQueryClient } from '@tanstack/react-query'

/**
 * AgentChat — Right sidebar AI chat panel.
 *
 * Uses Supabase Realtime for message updates (Database as Message Bus).
 * Fetches history via useProjectChat (React Query).
 */
export function AgentChat({ projectId }: { projectId: string }) {
  const [input, setInput] = useState('')
  const chatEndRef = useRef<HTMLDivElement>(null)
  
  // Custom hook for Realtime subscription
  useRealtimeSubscription(
    'chat_messages',
    `project_id=eq.${projectId}`,
    chatKeys.list(projectId)
  )

  const { data: messages, isLoading } = useProjectChat(projectId)
  const runAgent = useRunAgent()
  const activeAgent = useBuilderStore((s) => s.activeAgent)
  const queryClient = useQueryClient()

  // Auto-scroll to bottom
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSend = useCallback(async () => {
    const trimmed = input.trim()
    if (!trimmed || runAgent.isPending) return

    setInput('')

    // 1. Optimistic UI Update
    const optimisticMsg: ChatMessage = {
      id: `temp-${Date.now()}`,
      project_id: projectId,
      role: 'user',
      content: trimmed,
      is_thinking: false,
      created_at: new Date().toISOString(),
    }

    queryClient.setQueryData(
      chatKeys.list(projectId),
      (old: ChatMessage[] | undefined) => [...(old || []), optimisticMsg]
    )

    try {
      const agentType: AgentType = activeAgent ?? 'code'
      
      // 2. Trigger Agent (Backend will log the user message to DB)
      await runAgent.mutateAsync({
        project_id: projectId,
        agent_type: agentType,
        input_context: { user_message: trimmed },
      })
      
      // We don't need to manually invalidate here because 
      // the backend write will trigger the Realtime subscription event
      
    } catch {
      // Revert optimistic update on error
      queryClient.setQueryData(
        chatKeys.list(projectId),
        (old: ChatMessage[] | undefined) => 
          old?.filter((m) => m.id !== optimisticMsg.id)
      )
      // Show error toast or message
      console.error('Failed to send message')
    }
  }, [input, projectId, activeAgent, runAgent, queryClient])

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const isProcessing = runAgent.isPending

  // Default welcome message if no history
  const displayMessages = messages && messages.length > 0 ? messages : [
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hello! I'm ready to help you build. What would you like me to work on?",
      created_at: new Date().toISOString(),
    } as ChatMessage
  ]

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
        </div>
        <div className="flex items-center gap-1">
          <button
            className="text-muted-foreground hover:text-foreground p-1 rounded hover:bg-muted"
            aria-label="Chat history"
          >
            <History className="size-4" />
          </button>
        </div>
      </div>

      {/* Chat messages */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-4 flex flex-col gap-4">
        {displayMessages.map((msg) =>
          msg.role === 'assistant' || msg.role === 'system' ? (
            <div key={msg.id} className="flex gap-3">
              <div className="size-8 shrink-0 rounded-full bg-cf-primary/10 flex items-center justify-center text-cf-primary">
                <Bot className="size-4" />
              </div>
              <div className="flex flex-col gap-1">
                <div className="text-xs text-muted-foreground">
                  <span className="hidden dark:inline">
                   {msg.role === 'system' ? 'System' : 'Code Agent'}
                  </span>
                  <span className="inline dark:hidden font-semibold text-foreground">
                    CodeForge AI
                  </span>
                </div>
                <div className={`p-3 rounded-lg rounded-tl-none border border-border text-sm shadow-sm whitespace-pre-wrap ${
                  msg.role === 'system' 
                    ? 'bg-muted/30 text-muted-foreground font-mono text-xs' 
                    : 'bg-card dark:bg-muted/50 text-foreground/80'
                }`}>
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
        
        {/* Loading Indicator */}
        {isProcessing && (
           <div className="flex gap-3">
             <div className="size-8 shrink-0 rounded-full bg-cf-primary/10 flex items-center justify-center text-cf-primary">
               <Loader2 className="size-4 animate-spin" />
             </div>
             <div className="flex flex-col gap-1">
                <div className="text-xs text-muted-foreground">Thinking...</div>
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
          {/* Send Button */}
          <div className="absolute right-2 bottom-2 flex items-center gap-1">
            <button
              onClick={handleSend}
              disabled={isProcessing || !input.trim()}
              className="p-1.5 bg-cf-primary text-black rounded-md hover:brightness-110 transition-colors shadow-sm disabled:opacity-50"
              aria-label="Send message"
            >
              <Send className="size-4" />
            </button>
          </div>
        </div>
      </div>
    </aside>
  )
}
