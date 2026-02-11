'use client'

import { useState, useCallback } from 'react'
import Editor from '@monaco-editor/react'
import { useTheme } from 'next-themes'
import { 
  FileJson, 
  FileCode2, 
  FileText, 
  Trash2, 
  ChevronDown, 
  ChevronUp,
  Play,
  Loader2,
  X
} from 'lucide-react'

interface CodeFile {
  name: string
  language: string
  content: string
}

interface LabCodeEditorProps {
  /** Files to display in tabs */
  files?: CodeFile[]
  /** Initial active file index */
  activeFileIndex?: number
  /** Callback when code changes */
  onChange?: (content: string, fileName: string) => void
  /** Callback when run button is clicked */
  onRun?: (fileName: string, content: string) => void
  /** Console output lines */
  consoleOutput?: string[]
  /** Is code currently running */
  isRunning?: boolean
  /** Read-only mode */
  readOnly?: boolean
  /** Height of the editor (excluding console) */
  editorHeight?: string
}

// Default demo files if none provided
const defaultFiles: CodeFile[] = [
  {
    name: 'solution.py',
    language: 'python',
    content: `def fibonacci(n):
    """Calculate the nth Fibonacci number."""
    # Check for negative input
    if n < 0:
        print("Incorrect input")
        return None

    # Base cases
    elif n == 0:
        return 0
    elif n == 1:
        return 1

    else:
        # TODO: Implement iterative approach for better performance
        return fibonacci(n-1) + fibonacci(n-2)


# Test the function
if __name__ == "__main__":
    print(f"fibonacci(10) = {fibonacci(10)}")
`,
  },
  {
    name: 'tests.py',
    language: 'python',
    content: `import unittest
from solution import fibonacci

class TestFibonacci(unittest.TestCase):
    def test_base_cases(self):
        self.assertEqual(fibonacci(0), 0)
        self.assertEqual(fibonacci(1), 1)

    def test_fibonacci_sequence(self):
        self.assertEqual(fibonacci(5), 5)
        self.assertEqual(fibonacci(10), 55)

    def test_negative_input(self):
        self.assertIsNone(fibonacci(-1))

if __name__ == '__main__':
    unittest.main()
`,
  },
]

const defaultConsoleOutput = [
  '$ python solution.py',
  '➜ Running tests...',
]

// File icon helper
function getFileIcon(fileName: string) {
  const ext = fileName.split('.').pop()?.toLowerCase()
  switch (ext) {
    case 'py':
      return <FileCode2 className="size-4 text-yellow-500" />
    case 'ts':
    case 'tsx':
      return <FileCode2 className="size-4 text-blue-500" />
    case 'js':
    case 'jsx':
      return <FileJson className="size-4 text-yellow-400" />
    case 'sql':
      return <FileJson className="size-4 text-orange-400" />
    case 'md':
      return <FileText className="size-4 text-muted-foreground" />
    default:
      return <FileCode2 className="size-4 text-muted-foreground" />
  }
}

/**
 * LabCodeEditor — Monaco-based editor for the Module Lab.
 *
 * Features:
 * - Multi-file tabs
 * - Syntax highlighting via Monaco
 * - Integrated console/terminal output
 * - Run button with loading state
 * - Dark/light theme support
 */
export function CodeEditor({
  files = defaultFiles,
  activeFileIndex = 0,
  onChange,
  onRun,
  consoleOutput = defaultConsoleOutput,
  isRunning = false,
  readOnly = false,
  editorHeight = 'flex-1',
}: LabCodeEditorProps) {
  const { resolvedTheme } = useTheme()
  const [activeTab, setActiveTab] = useState(activeFileIndex)
  const [isConsoleOpen, setIsConsoleOpen] = useState(true)
  const [fileContents, setFileContents] = useState<Record<string, string>>(
    Object.fromEntries(files.map((f) => [f.name, f.content]))
  )

  const activeFile = files[activeTab]
  const monacoTheme = resolvedTheme === 'dark' ? 'vs-dark' : 'light'

  const handleEditorChange = useCallback(
    (value: string | undefined) => {
      if (value === undefined) return
      const fileName = activeFile.name
      setFileContents((prev) => ({ ...prev, [fileName]: value }))
      onChange?.(value, fileName)
    },
    [activeFile, onChange]
  )

  const handleRun = () => {
    const fileName = activeFile.name
    onRun?.(fileName, fileContents[fileName])
  }

  return (
    <div className="flex flex-1 flex-col min-h-0 min-w-0">
      {/* Tab bar with run button */}
      <div className="flex items-center justify-between border-b border-border bg-muted/30 shrink-0">
        {/* Tabs */}
        <div className="flex items-center overflow-x-auto">
          {files.map((file, i) => (
            <button
              key={file.name}
              onClick={() => setActiveTab(i)}
              className={`flex items-center gap-2 px-4 py-2.5 text-xs font-mono transition-colors border-b-2 ${
                i === activeTab
                  ? 'border-cf-primary bg-background text-foreground'
                  : 'border-transparent text-muted-foreground hover:text-foreground hover:bg-muted/50'
              }`}
            >
              {getFileIcon(file.name)}
              {file.name}
              {i === activeTab && (
                <span className="ml-1 p-0.5 hover:bg-muted rounded">
                  <X className="size-3 text-muted-foreground" />
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Run button */}
        <button
          onClick={handleRun}
          disabled={isRunning}
          className="flex items-center gap-2 px-4 py-1.5 mr-2 bg-cf-primary hover:bg-cf-primary/90 text-white rounded text-xs font-medium transition-colors disabled:opacity-50"
        >
          {isRunning ? (
            <>
              <Loader2 className="size-3.5 animate-spin" />
              Running...
            </>
          ) : (
            <>
              <Play className="size-3.5" />
              Run
            </>
          )}
        </button>
      </div>

      {/* Monaco Editor */}
      <div className={editorHeight} style={{ minHeight: 0 }}>
        <Editor
          height="100%"
          language={activeFile.language}
          value={fileContents[activeFile.name]}
          theme={monacoTheme}
          onChange={handleEditorChange}
          options={{
            readOnly,
            minimap: { enabled: false },
            fontSize: 14,
            lineNumbers: 'on',
            scrollBeyondLastLine: false,
            automaticLayout: true,
            tabSize: 4,
            wordWrap: 'on',
            padding: { top: 16, bottom: 16 },
            renderLineHighlight: 'line',
            cursorBlinking: 'smooth',
            fontFamily: 'JetBrains Mono, Menlo, Monaco, Consolas, monospace',
            fontLigatures: true,
          }}
        />
      </div>

      {/* Console Panel */}
      <div
        className={`border-t border-border bg-muted/20 flex flex-col shrink-0 transition-all ${
          isConsoleOpen ? 'h-40' : 'h-10'
        }`}
      >
        {/* Console header */}
        <button
          onClick={() => setIsConsoleOpen(!isConsoleOpen)}
          className="flex items-center justify-between px-4 py-2 border-b border-border bg-muted/30 hover:bg-muted/50 transition-colors"
        >
          <span className="text-xs font-bold text-muted-foreground uppercase tracking-wide">
            Console
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation()
                // Clear console would go here
              }}
              className="p-1 hover:bg-muted rounded"
              aria-label="Clear console"
            >
              <Trash2 className="size-3.5 text-muted-foreground" />
            </button>
            {isConsoleOpen ? (
              <ChevronDown className="size-4 text-muted-foreground" />
            ) : (
              <ChevronUp className="size-4 text-muted-foreground" />
            )}
          </div>
        </button>

        {/* Console output */}
        {isConsoleOpen && (
          <div className="flex-1 p-3 font-mono text-xs overflow-y-auto custom-scrollbar">
            {consoleOutput.map((line, i) => (
              <div key={i} className="flex gap-2 mb-1">
                {line.startsWith('$') ? (
                  <>
                    <span className="text-muted-foreground select-none">$</span>
                    <span className="text-foreground">{line.slice(2)}</span>
                  </>
                ) : line.startsWith('➜') ? (
                  <>
                    <span className="text-emerald-500 select-none">➜</span>
                    <span className="text-muted-foreground">{line.slice(2)}</span>
                  </>
                ) : line.startsWith('✖') ? (
                  <>
                    <span className="text-red-500 select-none">✖</span>
                    <span className="text-red-500">{line.slice(2)}</span>
                  </>
                ) : line.startsWith('✓') ? (
                  <>
                    <span className="text-emerald-500 select-none">✓</span>
                    <span className="text-emerald-500">{line.slice(2)}</span>
                  </>
                ) : (
                  <span className="text-muted-foreground">{line}</span>
                )}
              </div>
            ))}
            {isRunning && (
              <div className="flex items-center gap-2 mt-2">
                <Loader2 className="size-3 animate-spin text-cf-primary" />
                <span className="text-muted-foreground">Executing...</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
