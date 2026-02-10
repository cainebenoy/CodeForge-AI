'use client'

import { useCallback, useRef } from 'react'
import Editor, { type OnMount } from '@monaco-editor/react'
import { useTheme } from 'next-themes'
import { useBuilderStore } from '@/store/useBuilderStore'
import { useUpdateFile } from '@/lib/hooks/use-files'
import { FileCode } from 'lucide-react'

/** Map file extensions to Monaco language identifiers */
function getLanguage(filePath: string): string {
  const ext = filePath.split('.').pop()?.toLowerCase() ?? ''
  const map: Record<string, string> = {
    ts: 'typescript',
    tsx: 'typescript',
    js: 'javascript',
    jsx: 'javascript',
    json: 'json',
    css: 'css',
    html: 'html',
    md: 'markdown',
    py: 'python',
    yaml: 'yaml',
    yml: 'yaml',
    sh: 'shell',
    bash: 'shell',
    sql: 'sql',
    graphql: 'graphql',
    dockerfile: 'dockerfile',
  }
  return map[ext] ?? 'plaintext'
}

/**
 * EditorPane — Monaco Editor integrated code editor.
 *
 * Reads the active file from Zustand store, renders it in Monaco,
 * and debounce-saves changes back to the store + API.
 */
export function EditorPane({ projectId }: { projectId: string }) {
  const activeFile = useBuilderStore((s) => s.activeFile)
  const generatedFiles = useBuilderStore((s) => s.generatedFiles)
  const updateStoreFile = useBuilderStore((s) => s.updateFile)
  const { resolvedTheme } = useTheme()
  const saveTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const { mutate: saveToApi } = useUpdateFile(projectId)

  const content = activeFile ? (generatedFiles[activeFile] ?? '') : ''
  const language = activeFile ? getLanguage(activeFile) : 'plaintext'

  const handleEditorMount: OnMount = (editor) => {
    // Focus editor on mount
    editor.focus()
  }

  const handleChange = useCallback(
    (value: string | undefined) => {
      if (!activeFile || value === undefined) return

      // Update Zustand store immediately
      updateStoreFile(activeFile, value)

      // Debounced save to API (1.5s after last keystroke)
      if (saveTimerRef.current) clearTimeout(saveTimerRef.current)
      saveTimerRef.current = setTimeout(() => {
        saveToApi({
          path: activeFile,
          payload: { content: value, language },
        })
      }, 1500)
    },
    [activeFile, updateStoreFile, saveToApi, language],
  )

  // Empty state when no file is selected
  if (!activeFile) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center bg-background dark:bg-black text-muted-foreground gap-4">
        <FileCode className="size-16 opacity-20" />
        <p className="text-sm">Select a file to start editing</p>
        <p className="text-xs text-muted-foreground/60">
          or run an agent to generate code
        </p>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-hidden bg-background dark:bg-black">
      <Editor
        height="100%"
        language={language}
        value={content}
        theme={resolvedTheme === 'dark' ? 'vs-dark' : 'light'}
        onChange={handleChange}
        onMount={handleEditorMount}
        options={{
          fontSize: 14,
          fontFamily: "'JetBrains Mono', 'Fira Code', 'Cascadia Code', monospace",
          lineNumbers: 'on',
          minimap: { enabled: true },
          scrollBeyondLastLine: false,
          wordWrap: 'on',
          tabSize: 2,
          automaticLayout: true,
          bracketPairColorization: { enabled: true },
          smoothScrolling: true,
          cursorBlinking: 'smooth',
          cursorSmoothCaretAnimation: 'on',
          padding: { top: 12, bottom: 12 },
          renderWhitespace: 'selection',
          suggest: { preview: true },
        }}
        loading={
          <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
            Loading editor...
          </div>
        }
      />
    </div>
  )
}
