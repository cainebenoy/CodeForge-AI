'use client'

import {
  useQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query'
import { studentApi } from '@/lib/api'
import type {
  RoadmapCreate,
  RoadmapProgressUpdate,
  SessionCreate,
  ChoiceFrameworkRequest,
  ChoiceFramework,
  ChoiceSelection,
  StudentProgress,
} from '@/types/api.types'

// ── Query keys ──
export const studentKeys = {
  roadmap: (projectId: string) => ['student', projectId, 'roadmap'] as const,
  sessions: (projectId: string) => ['student', projectId, 'sessions'] as const,
  progress: (projectId: string) => ['student', projectId, 'progress'] as const,
}

/**
 * Get the learning roadmap for a project.
 */
export function useRoadmap(projectId: string) {
  return useQuery({
    queryKey: studentKeys.roadmap(projectId),
    queryFn: () => studentApi.getRoadmap(projectId),
    enabled: !!projectId,
  })
}

/**
 * Generate a new learning roadmap.
 */
export function useCreateRoadmap(projectId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: RoadmapCreate) => studentApi.createRoadmap(projectId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: studentKeys.roadmap(projectId) })
    },
  })
}

/**
 * Mark a roadmap step as completed.
 */
export function useUpdateRoadmapProgress(projectId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: RoadmapProgressUpdate) => studentApi.updateProgress(projectId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: studentKeys.roadmap(projectId) })
      queryClient.invalidateQueries({ queryKey: studentKeys.progress(projectId) })
    },
  })
}

/**
 * Record a study session.
 */
export function useCreateSession(projectId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: SessionCreate) => studentApi.createSession(projectId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: studentKeys.sessions(projectId) })
      queryClient.invalidateQueries({ queryKey: studentKeys.progress(projectId) })
    },
  })
}

/**
 * List study sessions for a project.
 */
export function useSessions(projectId: string, limit?: number) {
  return useQuery({
    queryKey: studentKeys.sessions(projectId),
    queryFn: () => studentApi.listSessions(projectId, limit),
    enabled: !!projectId,
  })
}

/**
 * Generate a choice framework for a module decision.
 */
export function useChoiceFramework(projectId: string) {
  return useMutation<ChoiceFramework, Error, ChoiceFrameworkRequest>({
    mutationFn: (payload) => studentApi.getChoiceFramework(projectId, payload),
  })
}

/**
 * Submit the student's choice selection.
 */
export function useSelectChoice(projectId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: ChoiceSelection) => studentApi.selectChoice(projectId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: studentKeys.roadmap(projectId) })
    },
  })
}

/**
 * Get computed progress for a student project.
 */
export function useStudentProgress(projectId: string) {
  return useQuery<StudentProgress>({
    queryKey: studentKeys.progress(projectId),
    queryFn: () => studentApi.getProgress(projectId),
    enabled: !!projectId,
  })
}
