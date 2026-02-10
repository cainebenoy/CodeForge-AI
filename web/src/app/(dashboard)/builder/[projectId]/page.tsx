import {
  BuilderHeader,
  BuilderFileTree,
  AgentChat,
  StatusBar,
  ActivityBar,
  TerminalPanel,
} from '@/components/features/builder'
import { EditorTabs, EditorPane } from '@/components/features/editor'

/**
 * Builder IDE page — full-screen code editor experience.
 *
 * DARK layout:  Header → [ FileTree | EditorTabs+Editor | AgentChat ] → StatusBar
 * LIGHT layout: Header → [ ActivityBar | FileTree | EditorTabs+Editor+Terminal | AgentChat ] → StatusBar
 *
 * The nested layout.tsx strips the DashboardNavbar so this takes the full viewport.
 */
export default function BuilderProjectPage({
  params,
}: {
  params: { projectId: string }
}) {
  return (
    <div className="flex flex-col h-screen overflow-hidden bg-background text-foreground">
      {/* ── Header ── */}
      <BuilderHeader projectName={`project-${params.projectId}`} />

      {/* ── Main IDE Body ── */}
      <div className="flex flex-1 min-h-0">
        {/* Activity bar — light mode only */}
        <ActivityBar />

        {/* File Explorer */}
        <BuilderFileTree />

        {/* Editor area */}
        <div className="flex flex-col flex-1 min-w-0">
          <EditorTabs />
          <EditorPane />
          {/* Terminal — light mode only */}
          <TerminalPanel />
        </div>

        {/* AI Chat sidebar */}
        <AgentChat />
      </div>

      {/* ── Status Bar ── */}
      <StatusBar />
    </div>
  )
}
