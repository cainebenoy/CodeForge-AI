'use client'

import { useState, useEffect, useCallback, useRef } from 'react'
import {
  useQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query'
import { agentApi } from '@/lib/api'
import { projectKeys } from './use-project'
import type {
  AgentRequest,
  AgentResponse,
  JobStatus,
  PaginatedResponse,
  ClarificationAnswer,
  SSEEvent,
} from '@/types/api.types'

// ── Query keys ──
export const jobKeys = {
  all: ['jobs'] as const,
  lists: (projectId: string) => [...jobKeys.all, 'list', projectId] as const,
  detail: (jobId: string) => [...jobKeys.all, 'detail', jobId] as const,
}

export const chatKeys = {
  list: (projectId: string) => ['chat', projectId] as const,
}

/**
 * Get chat history for a project.
 */
export function useProjectChat(projectId: string) {
  return useQuery({
    queryKey: chatKeys.list(projectId),
    queryFn: async () => {
      const { createClient } = await import('@/lib/supabase/client')
      const supabase = createClient()
      const { data, error } = await supabase
        .from('chat_messages')
        .select('*')
        .eq('project_id', projectId)
        .order('created_at', { ascending: true })
      
      if (error) throw error
      return data as import('@/types/api.types').ChatMessage[]
    },
    enabled: !!projectId,
  })
}


/**
 * Get the status of a single agent job.
 * Auto-refetches every 3s while the job is running or queued.
 */
export function useJobStatus(jobId: string | null) {
  return useQuery<JobStatus>({
    queryKey: jobKeys.detail(jobId ?? ''),
    queryFn: () => agentApi.getJobStatus(jobId!),
    enabled: !!jobId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'running' || status === 'queued' || status === 'waiting_for_input') {
        return 3000
      }
      return false
    },
  })
}

/**
 * List jobs for a project (paginated).
 */
export function useProjectJobs(projectId: string, params?: { page?: number; page_size?: number }) {
  return useQuery<PaginatedResponse<JobStatus>>({
    queryKey: jobKeys.lists(projectId),
    queryFn: () => agentApi.listJobs(projectId, params),
    enabled: !!projectId,
  })
}

/**
 * Trigger a single agent. Returns job_id for tracking.
 * Invalidates job list and project detail on success.
 */
export function useRunAgent() {
  const queryClient = useQueryClient()

  return useMutation<AgentResponse, Error, AgentRequest>({
    mutationFn: (payload) => agentApi.runAgent(payload),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: jobKeys.lists(variables.project_id) })
      // The project spec may be updated after agent completes
      queryClient.invalidateQueries({ queryKey: projectKeys.detail(variables.project_id) })
    },
  })
}

/**
 * Trigger the full builder pipeline.
 */
export function useRunPipeline() {
  const queryClient = useQueryClient()

  return useMutation<AgentResponse, Error, AgentRequest>({
    mutationFn: (payload) => agentApi.runPipeline(payload),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ queryKey: jobKeys.lists(variables.project_id) })
      queryClient.invalidateQueries({ queryKey: projectKeys.detail(variables.project_id) })
    },
  })
}

/**
 * Respond to agent clarification questions.
 */
export function useRespondToAgent() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ jobId, payload }: { jobId: string; payload: ClarificationAnswer }) =>
      agentApi.respondToAgent(jobId, payload),
    onSuccess: (_, { jobId }) => {
      queryClient.invalidateQueries({ queryKey: jobKeys.detail(jobId) })
    },
  })
}

/**
 * Cancel a running/queued agent job.
 */
export function useCancelJob() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (jobId: string) => agentApi.cancelJob(jobId),
    onSuccess: (_, jobId) => {
      queryClient.invalidateQueries({ queryKey: jobKeys.detail(jobId) })
    },
  })
}

/**
 * SSE streaming hook — connects to the agent job stream endpoint.
 *
 * Returns parsed SSE events for real-time progress, completion,
 * and error updates without polling.
 *
 * Security: uses the stream URL directly (no auth header needed on
 * SSE connections since the job_id acts as an opaque capability token).
 */
export function useJobStream(jobId: string | null) {
  const [events, setEvents] = useState<SSEEvent[]>([])
  const [latestEvent, setLatestEvent] = useState<SSEEvent | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const eventSourceRef = useRef<EventSource | null>(null)
  const queryClient = useQueryClient()

  const disconnect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
      setIsConnected(false)
    }
  }, [])

  useEffect(() => {
    if (!jobId) return

    const url = agentApi.getStreamUrl(jobId)
    const es = new EventSource(url)
    eventSourceRef.current = es

    es.onopen = () => setIsConnected(true)

    es.onmessage = (event) => {
      try {
        const parsed: SSEEvent = JSON.parse(event.data)
        setEvents((prev) => [...prev, parsed])
        setLatestEvent(parsed)

        // On terminal states, close the connection and refresh cached data
        if (parsed.status === 'completed' || parsed.status === 'failed') {
          queryClient.invalidateQueries({ queryKey: jobKeys.detail(jobId) })
          es.close()
          setIsConnected(false)
        }
      } catch {
        // Skip malformed events
      }
    }

    es.onerror = () => {
      es.close()
      setIsConnected(false)
    }

    return () => {
      es.close()
      setIsConnected(false)
    }
  }, [jobId, queryClient])

  return { events, latestEvent, isConnected, disconnect }
}
