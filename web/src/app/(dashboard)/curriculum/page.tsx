'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import {
  SkillTreeHeader,
  SkillTreeCanvas,
  ModuleSidebar,
} from '@/components/features/curriculum'
import { useRoadmap, useStudentProgress } from '@/lib/hooks/use-student'
import { useStudentStore } from '@/store/useStudentStore'
import { Loader2 } from 'lucide-react'

/**
 * Skill Tree / Curriculum page.
 *
 * Reads the active student project from the Zustand store and fetches
 * the roadmap/progress from the API. Falls back to demo UI when no
 * project is selected or API unavailable.
 *
 * Route: /dashboard/curriculum
 */
export default function CurriculumPage() {
  const router = useRouter()
  const activeProjectId = useStudentStore((s) => s.activeProjectId)
  const currentModuleIndex = useStudentStore((s) => s.currentModuleIndex)
  const setCurrentModule = useStudentStore((s) => s.setCurrentModule)

  // Fetch roadmap and progress if we have an active project
  const { data: roadmap, isLoading: roadmapLoading } = useRoadmap(activeProjectId ?? '')
  const { data: progress, isLoading: progressLoading } = useStudentProgress(activeProjectId ?? '')

  return (
    <div className="flex flex-col h-screen overflow-hidden bg-background text-foreground">
      <SkillTreeHeader
        progress={progress?.percent_complete}
        level={progress ? Math.floor(progress.completed_modules / 2) + 1 : undefined}
        xp={progress ? progress.completed_modules * 350 : undefined}
      />

      <div className="flex flex-1 relative overflow-hidden">
        <SkillTreeCanvas
          modules={roadmap?.modules}
          currentModuleIndex={currentModuleIndex}
          completedModules={progress?.completed_modules ?? 0}
        />
        <ModuleSidebar
          module={roadmap?.modules?.[currentModuleIndex]}
          moduleIndex={currentModuleIndex}
          projectId={activeProjectId ?? undefined}
          progress={progress}
          onLaunchLab={() => {
            if (activeProjectId) {
              router.push(`/lab/${activeProjectId}`)
            }
          }}
        />
      </div>
    </div>
  )
}
