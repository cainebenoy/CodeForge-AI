'use client'

import dynamic from 'next/dynamic'
import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import { useTheme } from 'next-themes'

// Dynamic import to prevent SSR issues with Sandpack
const SandpackProvider = dynamic(
  () => import('@codesandbox/sandpack-react').then((mod) => mod.SandpackProvider),
  { ssr: false }
)
const SandpackLayout = dynamic(
  () => import('@codesandbox/sandpack-react').then((mod) => mod.SandpackLayout),
  { ssr: false }
)
const SandpackCodeEditor = dynamic(
  () => import('@codesandbox/sandpack-react').then((mod) => mod.SandpackCodeEditor),
  { ssr: false }
)
const SandpackPreview = dynamic(
  () => import('@codesandbox/sandpack-react').then((mod) => mod.SandpackPreview),
  { ssr: false }
)

type SandpackTemplate = 'react' | 'react-ts' | 'vanilla' | 'vanilla-ts' | 'vue' | 'vue-ts' | 'angular' | 'node'

interface SandpackWrapperProps {
  /** Files to display in the sandbox */
  files?: Record<string, string>
  /** Template to use (react, react-ts, node, etc.) */
  template?: SandpackTemplate
  /** Initial active file path */
  activeFile?: string
  /** Show/hide preview panel */
  showPreview?: boolean
  /** Show/hide console panel */
  showConsole?: boolean
  /** Read-only mode */
  readOnly?: boolean
  /** Height of the sandbox */
  height?: string | number
  /** Callback when file content changes */
  onCodeChange?: (code: string, file: string) => void
  /** Custom className */
  className?: string
}

/**
 * SandpackWrapper — In-browser code execution sandbox for Student Mode.
 * 
 * Wraps @codesandbox/sandpack-react with:
 * - Dynamic SSR-safe imports
 * - Theme integration (light/dark)
 * - Custom file injection from roadmap/module content
 * - Code change callbacks
 */
export function SandpackWrapper({
  files,
  template = 'react',
  activeFile,
  showPreview = true,
  showConsole = false,
  readOnly = false,
  height = '400px',
  onCodeChange,
  className = '',
}: SandpackWrapperProps) {
  const { resolvedTheme } = useTheme()
  const [isLoaded, setIsLoaded] = useState(false)

  // Default files based on template
  const defaultFiles: Record<string, string> = {
    '/App.js': `export default function App() {
  return (
    <div className="app">
      <h1>Hello CodeForge!</h1>
      <p>Start coding and see the result instantly.</p>
    </div>
  );
}`,
    '/styles.css': `body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  margin: 0;
  padding: 20px;
  background: #f8f9fa;
}
.app {
  max-width: 600px;
  margin: 0 auto;
}
h1 {
  color: #10b981;
}`,
  }

  const sandpackFiles = files || defaultFiles

  // Sandpack theme based on system theme
  const sandpackTheme = resolvedTheme === 'dark' ? 'dark' : 'light'

  return (
    <div className={`relative rounded-lg overflow-hidden border border-border ${className}`} style={{ height }}>
      {/* Loading overlay */}
      {!isLoaded && (
        <div className="absolute inset-0 flex items-center justify-center bg-background z-10">
          <div className="flex flex-col items-center gap-2">
            <Loader2 className="size-6 animate-spin text-cf-primary" />
            <span className="text-sm text-muted-foreground">Loading sandbox...</span>
          </div>
        </div>
      )}

      <SandpackProvider
        template={template}
        files={sandpackFiles}
        theme={sandpackTheme}
        options={{
          activeFile: activeFile || Object.keys(sandpackFiles)[0],
          recompileMode: 'delayed',
          recompileDelay: 500,
          autorun: true,
          autoReload: true,
        }}
      >
        <SandpackLayout
          style={{ height: '100%' }}
        >
          <SandpackCodeEditor
            showTabs
            showLineNumbers
            showInlineErrors
            wrapContent
            readOnly={readOnly}
            style={{ flex: 1, minWidth: 0 }}
          />
          {showPreview && (
            <SandpackPreview
              showOpenInCodeSandbox={false}
              showRefreshButton
              style={{ flex: 1, minWidth: 0 }}
            />
          )}
        </SandpackLayout>
        {/* Hidden element to detect when Sandpack has loaded */}
        <div
          ref={(el) => {
            if (el && !isLoaded) {
              // Small delay to ensure Sandpack is ready
              setTimeout(() => setIsLoaded(true), 100)
            }
          }}
        />
      </SandpackProvider>
    </div>
  )
}

/**
 * SandpackPreviewOnly — Just the preview without editor.
 * Useful for showing the result of generated code.
 */
export function SandpackPreviewOnly({
  files,
  template = 'react',
  height = '300px',
  className = '',
}: Pick<SandpackWrapperProps, 'files' | 'template' | 'height' | 'className'>) {
  const { resolvedTheme } = useTheme()
  const sandpackTheme = resolvedTheme === 'dark' ? 'dark' : 'light'

  return (
    <div className={`relative rounded-lg overflow-hidden border border-border ${className}`} style={{ height }}>
      <SandpackProvider template={template} files={files} theme={sandpackTheme}>
        <SandpackPreview
          showOpenInCodeSandbox={false}
          showRefreshButton
          style={{ height: '100%' }}
        />
      </SandpackProvider>
    </div>
  )
}
