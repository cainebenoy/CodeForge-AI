'use client'

import { useEffect, useRef } from 'react'
import {
  LabHeader,
  InstructionPanel,
  CodeEditor,
  MentorChat,
  LabFooter,
} from '@/components/features/lab'
import { useProject } from '@/lib/hooks/use-project'
import { useRoadmap, useCreateSession } from '@/lib/hooks/use-student'
import { useStudentStore } from '@/store/useStudentStore'
import { useParams } from 'next/navigation'

/**
 * Module Lab page — interactive coding environment with AI mentor.
 *
 * Wire up with project data, roadmap module info, and session tracking.
 * Falls back to demo data when API unavailable.
 *
 * Route: /dashboard/lab/[projectId]
 */
export default function LabPage() {
  const params = useParams<{ projectId: string }>()
  const projectId = params.projectId

  const { data: project } = useProject(projectId)
  const { data: roadmap } = useRoadmap(projectId)
  const createSession = useCreateSession(projectId)

  // Set active project in student store for sidebar context
  const setActiveProjectId = useStudentStore((s) => s.setActiveProjectId)
  const currentModuleIndex = useStudentStore((s) => s.currentModuleIndex)

  useEffect(() => {
    if (projectId) {
      setActiveProjectId(projectId)
    }
  }, [projectId, setActiveProjectId])

  // Track session start time for duration calculation
  const sessionStartRef = useRef(Date.now())

  // Get current module from roadmap
  const currentModule = roadmap?.modules?.[currentModuleIndex]

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-background text-foreground">
      <LabHeader
        projectTitle={project?.title}
        moduleTitle={currentModule?.title}
        moduleProgress={currentModule ? ((currentModuleIndex + 1) / (roadmap?.modules?.length ?? 1)) * 100 : undefined}
      />

      <main className="flex flex-1 overflow-hidden w-full">
        <InstructionPanel
          module={currentModule}
        />
        <CodeEditor />
        <MentorChat
          projectId={projectId}
        />
      </main>

      <LabFooter projectId={projectId} />
    </div>
  )
}
