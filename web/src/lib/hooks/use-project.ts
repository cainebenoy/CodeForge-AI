'use client'

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryOptions,
} from '@tanstack/react-query'
import { projectApi } from '@/lib/api'
import type {
  Project,
  ProjectCreate,
  ProjectUpdate,
  PaginatedResponse,
} from '@/types/api.types'

// ── Query keys ──
export const projectKeys = {
  all: ['projects'] as const,
  lists: () => [...projectKeys.all, 'list'] as const,
  list: (filters: Record<string, unknown>) => [...projectKeys.lists(), filters] as const,
  details: () => [...projectKeys.all, 'detail'] as const,
  detail: (id: string) => [...projectKeys.details(), id] as const,
}

/**
 * Fetch a paginated list of the current user's projects.
 */
export function useProjects(
  params?: { page?: number; page_size?: number; mode?: string; status?: string },
  options?: Partial<UseQueryOptions<PaginatedResponse<Project>>>,
) {
  return useQuery<PaginatedResponse<Project>>({
    queryKey: projectKeys.list(params ?? {}),
    queryFn: () => projectApi.list(params),
    ...options,
  })
}

/**
 * Fetch a single project by ID.
 */
export function useProject(projectId: string) {
  return useQuery<Project>({
    queryKey: projectKeys.detail(projectId),
    queryFn: () => projectApi.get(projectId),
    enabled: !!projectId,
  })
}

/**
 * Create a new project. On success, invalidates the project list cache.
 */
export function useCreateProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: ProjectCreate) => projectApi.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() })
    },
  })
}

/**
 * Update a project. On success, invalidates both detail and list caches.
 */
export function useUpdateProject(projectId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: ProjectUpdate) => projectApi.update(projectId, payload),
    onSuccess: (updatedProject) => {
      queryClient.setQueryData(projectKeys.detail(projectId), updatedProject)
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() })
    },
  })
}

/**
 * Delete (archive) a project. On success, removes from cache and invalidates list.
 */
export function useDeleteProject() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (projectId: string) => projectApi.delete(projectId),
    onSuccess: (_, projectId) => {
      queryClient.removeQueries({ queryKey: projectKeys.detail(projectId) })
      queryClient.invalidateQueries({ queryKey: projectKeys.lists() })
    },
  })
}
