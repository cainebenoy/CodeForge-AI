'use client'

import {
  useQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query'
import { projectApi } from '@/lib/api'
import type {
  CodeFile,
  CodeFileCreate,
  CodeFileUpdate,
  RefactorRequest,
  RefactorResult,
} from '@/types/api.types'

// ── Query keys ──
export const fileKeys = {
  all: (projectId: string) => ['files', projectId] as const,
  list: (projectId: string) => [...fileKeys.all(projectId), 'list'] as const,
  detail: (projectId: string, path: string) =>
    [...fileKeys.all(projectId), 'detail', path] as const,
}

/**
 * List all files for a project.
 */
export function useProjectFiles(projectId: string) {
  return useQuery({
    queryKey: fileKeys.list(projectId),
    queryFn: () => projectApi.listFiles(projectId),
    enabled: !!projectId,
  })
}

/**
 * Get a single file's content by path.
 */
export function useFileContent(projectId: string, filePath: string) {
  return useQuery<CodeFile>({
    queryKey: fileKeys.detail(projectId, filePath),
    queryFn: () => projectApi.getFile(projectId, filePath),
    enabled: !!projectId && !!filePath,
  })
}

/**
 * Create or upsert a file. Invalidates the file list cache on success.
 */
export function useCreateFile(projectId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: CodeFileCreate) => projectApi.createFile(projectId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: fileKeys.list(projectId) })
    },
  })
}

/**
 * Update a file's content. Updates both detail and list caches.
 */
export function useUpdateFile(projectId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ path, payload }: { path: string; payload: CodeFileUpdate }) =>
      projectApi.updateFile(projectId, path, payload),
    onSuccess: (updatedFile, { path }) => {
      queryClient.setQueryData(fileKeys.detail(projectId, path), updatedFile)
      queryClient.invalidateQueries({ queryKey: fileKeys.list(projectId) })
    },
  })
}

/**
 * Delete a file. Removes from cache and invalidates list.
 */
export function useDeleteFile(projectId: string) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (filePath: string) => projectApi.deleteFile(projectId, filePath),
    onSuccess: (_, filePath) => {
      queryClient.removeQueries({ queryKey: fileKeys.detail(projectId, filePath) })
      queryClient.invalidateQueries({ queryKey: fileKeys.list(projectId) })
    },
  })
}

/**
 * AI-powered code refactoring. Does not automatically invalidate caches
 * since the user may want to review before applying.
 */
export function useRefactorFile(projectId: string) {
  return useMutation<RefactorResult, Error, { path: string; payload: RefactorRequest; apply?: boolean }>({
    mutationFn: ({ path, payload, apply }) =>
      projectApi.refactorFile(projectId, path, payload, apply),
  })
}
