/**
 * Custom React Hook - useProject
 * Fetches project data using React Query
 */

import { useQuery } from '@tanstack/react-query'
import { projectApi } from '@/lib/api'

export function useProject(projectId: string) {
  return useQuery({
    queryKey: ['project', projectId],
    queryFn: () => projectApi.getProject(projectId),
    enabled: !!projectId,
  })
}
