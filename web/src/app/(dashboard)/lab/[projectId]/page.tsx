import {
  LabHeader,
  InstructionPanel,
  CodeEditor,
  MentorChat,
  LabFooter,
} from '@/components/features/lab'

/**
 * Module Lab page — interactive coding environment with AI mentor.
 *
 * **Dark**: Zinc-950 workspace — instruction sidebar (objectives + checkboxes),
 *           SQL code editor with terminal, Pedagogy Agent chat, action footer.
 * **Light**: White workspace — task panel with tabs, Python code editor with
 *            console output, AI Mentor chat with action buttons, action footer.
 *
 * Route: /dashboard/lab/[projectId]
 */
export default function LabPage() {
  return (
    <div className="flex flex-col h-screen overflow-hidden bg-background text-foreground">
      <LabHeader />

      <main className="flex flex-1 overflow-hidden w-full">
        <InstructionPanel />
        <CodeEditor />
        <MentorChat />
      </main>

      <LabFooter />
    </div>
  )
}
