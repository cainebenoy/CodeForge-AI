/**
 * Code Editor - Monaco Wrapper
 * Wraps @monaco-editor/react with custom theming
 */

'use client'

export function CodeEditor() {
  return (
    <div className="h-full rounded-lg border bg-card">
      <div className="p-4 text-sm text-muted-foreground">
        Monaco Editor will be integrated here
      </div>
    </div>
  )
}
