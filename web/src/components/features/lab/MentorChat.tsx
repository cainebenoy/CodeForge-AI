'use client'

import { useState } from 'react'
import { Brain, Send, MoreVertical, User } from 'lucide-react'

/* ─── Message types ─── */
interface ChatMessage {
  role: 'ai' | 'user'
  text: string
  time: string
  hint?: boolean
  actions?: { label: string; primary?: boolean }[]
}

const darkMessages: ChatMessage[] = [
  {
    role: 'ai',
    text: 'Hello! I see you\'re about to optimize the <code class="bg-zinc-700 px-1 py-0.5 rounded text-xs font-mono">users</code> table. Before you start, do you know which index type is default in PostgreSQL?',
    time: '10:42 AM',
  },
  {
    role: 'user',
    text: "I think it's B-Tree?",
    time: '10:43 AM',
  },
  {
    role: 'ai',
    text: 'Correct! B-Trees are excellent for equality and range queries. Since we are looking up by email, this is a perfect fit.',
    time: '10:44 AM',
    hint: true,
  },
]

const lightMessages: ChatMessage[] = [
  {
    role: 'ai',
    text: 'I noticed you hit a recursion limit. For larger values of <code class="bg-muted px-1 rounded text-xs">n</code>, simple recursion can be very slow.',
    time: '10:23 AM',
  },
  {
    role: 'ai',
    text: 'Would you like a hint on how to optimize this using memoization or an iterative approach?',
    time: '',
    actions: [
      { label: 'Yes, show hint', primary: true },
      { label: "No, I'll try" },
    ],
  },
  {
    role: 'user',
    text: "I'll try the iterative approach first.",
    time: '10:25 AM',
  },
]

/**
 * MentorChat — Right-side AI Mentor panel for the Module Lab.
 *
 * **Dark**: Pedagogy Agent header (violet gradient avatar, online badge),
 *           chat bubbles with rounded corners, "Need a hint?" link, text input.
 * **Light**: AI Mentor header with icon, rounded-2xl chat bubbles with avatars,
 *            action buttons inside AI messages, input with send.
 */
export function MentorChat() {
  const [input, setInput] = useState('')

  return (
    <>
      {/* ═══ DARK ═══ */}
      <aside className="hidden dark:flex w-[320px] shrink-0 border-l border-zinc-800 flex-col bg-zinc-950">
        {/* Header */}
        <div className="p-4 border-b border-zinc-800 flex items-center gap-3">
          <div className="relative">
            <div className="size-8 rounded bg-gradient-to-br from-violet-500 to-purple-600 flex items-center justify-center text-white shadow-lg shadow-violet-500/20">
              <Brain className="size-[18px]" />
            </div>
            <div className="absolute -bottom-1 -right-1 size-3 bg-emerald-500 border-2 border-zinc-950 rounded-full" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-foreground">Pedagogy Agent</h3>
            <p className="text-[10px] text-zinc-500 uppercase tracking-wide font-medium">
              Online • v2.4
            </p>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 p-4 overflow-y-auto custom-scrollbar space-y-4 bg-zinc-950">
          {darkMessages.map((msg, i) =>
            msg.role === 'ai' ? (
              <div key={i} className="flex flex-col gap-1 items-start">
                <div
                  className="bg-zinc-800/50 border border-zinc-700 text-zinc-200 text-sm p-3 rounded-lg rounded-tl-none max-w-[90%] shadow-sm"
                  dangerouslySetInnerHTML={{ __html: `<p>${msg.text}</p>` }}
                />
                {msg.hint && (
                  <p className="text-violet-400/80 text-xs font-medium cursor-pointer hover:underline flex items-center gap-1 ml-1 mt-1">
                    💡 Need a syntax hint?
                  </p>
                )}
                <span className="text-[10px] text-zinc-600 pl-1">{msg.time}</span>
              </div>
            ) : (
              <div key={i} className="flex flex-col gap-1 items-end">
                <div className="bg-violet-500/20 border border-violet-500/30 text-white text-sm p-3 rounded-lg rounded-tr-none max-w-[90%] shadow-sm">
                  <p>{msg.text}</p>
                </div>
                <span className="text-[10px] text-zinc-600 pr-1">{msg.time}</span>
              </div>
            ),
          )}
        </div>

        {/* Input */}
        <div className="p-4 border-t border-zinc-800 bg-zinc-950">
          <div className="relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask for a hint..."
              className="w-full bg-zinc-900 border border-zinc-700 rounded-sm py-2.5 pl-3 pr-10 text-sm text-foreground placeholder-zinc-500 focus:outline-none focus:border-violet-500 focus:ring-1 focus:ring-violet-500 transition-all"
            />
            <button
              className="absolute right-2 top-2 text-zinc-500 hover:text-violet-400 transition-colors"
              aria-label="Send message"
            >
              <Send className="size-5" />
            </button>
          </div>
          <p className="text-[10px] text-zinc-600 text-center mt-2">
            AI can make mistakes. Check important info.
          </p>
        </div>
      </aside>

      {/* ═══ LIGHT ═══ */}
      <section className="flex dark:hidden w-[320px] min-w-[280px] flex-col border-l border-border bg-white/80 backdrop-blur-md relative z-10">
        {/* Header */}
        <div className="p-4 border-b border-border flex items-center gap-3 bg-white/50">
          <div className="p-1.5 bg-blue-600/10 rounded-lg">
            <Brain className="size-5 text-blue-600" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-foreground">AI Mentor</h2>
            <p className="text-[10px] text-muted-foreground">Always here to help</p>
          </div>
          <button
            className="ml-auto p-1.5 hover:bg-muted rounded text-muted-foreground hover:text-foreground"
            aria-label="Options"
          >
            <MoreVertical className="size-[18px]" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gradient-to-b from-transparent to-white/30">
          {lightMessages.map((msg, i) =>
            msg.role === 'ai' ? (
              <div key={i} className="flex gap-3">
                <div className="size-8 rounded-full bg-blue-600/10 flex items-center justify-center shrink-0">
                  <Brain className="size-4 text-blue-600" />
                </div>
                <div className="flex flex-col gap-1 max-w-[85%]">
                  {msg.time && (
                    <span className="text-[10px] text-muted-foreground ml-1">
                      AI Mentor • {msg.time}
                    </span>
                  )}
                  <div className="bg-white border border-border rounded-2xl rounded-tl-none p-3 shadow-sm">
                    <p
                      className="text-xs text-muted-foreground leading-relaxed"
                      dangerouslySetInnerHTML={{ __html: msg.text }}
                    />
                    {msg.actions && (
                      <div className="mt-3 flex gap-2">
                        {msg.actions.map((a) => (
                          <button
                            key={a.label}
                            className={`px-3 py-1.5 text-[10px] font-semibold rounded border transition-colors ${
                              a.primary
                                ? 'bg-blue-600/5 hover:bg-blue-600/10 text-blue-600 border-blue-600/20'
                                : 'bg-muted/50 hover:bg-muted text-muted-foreground border-border'
                            }`}
                          >
                            {a.label}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div key={i} className="flex flex-row-reverse gap-3">
                <div className="size-8 rounded-full bg-muted overflow-hidden shrink-0 border border-border flex items-center justify-center">
                  <User className="size-4 text-muted-foreground" />
                </div>
                <div className="flex flex-col items-end gap-1 max-w-[85%]">
                  {msg.time && (
                    <span className="text-[10px] text-muted-foreground mr-1">
                      You • {msg.time}
                    </span>
                  )}
                  <div className="bg-blue-600 text-white rounded-2xl rounded-tr-none p-3 shadow-sm">
                    <p className="text-xs leading-relaxed">{msg.text}</p>
                  </div>
                </div>
              </div>
            ),
          )}
        </div>

        {/* Input */}
        <div className="p-4 border-t border-border bg-white/90">
          <div className="relative">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question..."
              className="w-full pl-4 pr-10 py-2.5 bg-muted/50 border border-border rounded text-sm focus:outline-none focus:ring-1 focus:ring-blue-600 focus:border-blue-600 placeholder-muted-foreground shadow-inner"
            />
            <button
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1 text-blue-600 hover:bg-blue-50 rounded-full transition-colors"
              aria-label="Send message"
            >
              <Send className="size-5" />
            </button>
          </div>
        </div>
      </section>
    </>
  )
}
