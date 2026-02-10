'use client'

import { useEffect } from 'react'
import {
  BuilderHeader,
  BuilderFileTree,
  AgentChat,
  StatusBar,
  ActivityBar,
  TerminalPanel,
} from '@/components/features/builder'
import { EditorTabs, EditorPane } from '@/components/features/editor'
import { useProject } from '@/lib/hooks/use-project'
import { useProjectFiles } from '@/lib/hooks/use-files'
import { useProjectRealtime } from '@/lib/hooks/use-realtime'
import { useBuilderStore } from '@/store/useBuilderStore'
import { Loader2 } from 'lucide-react'

/**
 * Builder IDE page — full-screen code editor experience.
 *
 * DARK layout:  Header → [ FileTree | EditorTabs+Editor | AgentChat ] → StatusBar
 * LIGHT layout: Header → [ ActivityBar | FileTree | EditorTabs+Editor+Terminal | AgentChat ] → StatusBar
 */
export default function BuilderProjectPage({
  params,
}: {
  params: { projectId: string }
}) {
  const { projectId } = params
  const { data: project, isLoading: projectLoading } = useProject(projectId)
  const { data: filesData } = useProjectFiles(projectId)
  const { clearFiles, addFile } = useBuilderStore()

  // Real-time: auto-refresh files, jobs, and project when DB changes
  useProjectRealtime(projectId)

  // Sync API files → Zustand store on load
  useEffect(() => {
    if (filesData?.files) {
      clearFiles()
      filesData.files.forEach((f) => addFile(f.path, f.content ?? ''))
    }
  }, [filesData, clearFiles, addFile])

  if (projectLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-background">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-background text-foreground">
      {/* ── Header ── */}
      <BuilderHeader projectName={project?.title ?? 'Untitled'} />

      {/* ── Main IDE Body ── */}
      <div className="flex flex-1 min-h-0">
        {/* Activity bar — light mode only */}
        <ActivityBar />

        {/* File Explorer */}
        <BuilderFileTree projectId={projectId} />

        {/* Editor area */}
        <div className="flex flex-col flex-1 min-w-0">
          <EditorTabs projectId={projectId} />
          <EditorPane projectId={projectId} />
          {/* Terminal — light mode only */}
          <TerminalPanel />
        </div>

        {/* AI Chat sidebar */}
        <AgentChat projectId={projectId} />
      </div>

      {/* ── Status Bar ── */}
      <StatusBar />
    </div>
  )
}
