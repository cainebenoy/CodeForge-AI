'use client'

import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { createClient } from '@/lib/supabase/client'
import { projectKeys } from './use-project'
import { fileKeys } from './use-files'
import { jobKeys } from './use-agents'
import type { RealtimeChannel } from '@supabase/supabase-js'

/**
 * Subscribe to real-time changes for a specific project.
 * Invalidates React Query caches when project data, files, or jobs change.
 *
 * Uses Supabase Realtime (Postgres Changes) — requires tables to be added
 * to the `supabase_realtime` publication in the database.
 */
export function useProjectRealtime(projectId: string | null) {
  const queryClient = useQueryClient()
  const channelRef = useRef<RealtimeChannel | null>(null)

  useEffect(() => {
    if (!projectId) return

    const supabase = createClient()

    const channel = supabase
      .channel(`project:${projectId}`)
      // ── Project row updates (status, specs, etc.) ──
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'projects',
          filter: `id=eq.${projectId}`,
        },
        () => {
          queryClient.invalidateQueries({ queryKey: projectKeys.detail(projectId) })
          queryClient.invalidateQueries({ queryKey: projectKeys.lists() })
        }
      )
      // ── Agent job changes (status, progress, result) ──
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'agent_jobs',
          filter: `project_id=eq.${projectId}`,
        },
        () => {
          queryClient.invalidateQueries({ queryKey: jobKeys.lists(projectId) })
        }
      )
      // ── File changes (create, update, delete) ──
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'project_files',
          filter: `project_id=eq.${projectId}`,
        },
        () => {
          queryClient.invalidateQueries({ queryKey: fileKeys.all(projectId) })
        }
      )
      .subscribe()

    channelRef.current = channel

    return () => {
      // Only remove if channel exists and is subscribed
      if (channelRef.current) {
        supabase.removeChannel(channelRef.current).catch(() => {
          // Ignore errors during cleanup (e.g., already disconnected)
        })
        channelRef.current = null
      }
    }
  }, [projectId, queryClient])
}

/**
 * Subscribe to real-time changes across all of the current user's projects.
 * Useful on the dashboard page to reflect new projects or status changes.
 */
export function useDashboardRealtime() {
  const queryClient = useQueryClient()
  const channelRef = useRef<RealtimeChannel | null>(null)

  useEffect(() => {
    const supabase = createClient()

    const channel = supabase
      .channel('dashboard')
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'public',
          table: 'projects',
        },
        () => {
          queryClient.invalidateQueries({ queryKey: projectKeys.all })
        }
      )
      .subscribe()

    channelRef.current = channel

    return () => {
      // Only remove if channel exists
      if (channelRef.current) {
        supabase.removeChannel(channelRef.current).catch(() => {
          // Ignore errors during cleanup
        })
        channelRef.current = null
      }
    }
  }, [queryClient])
}

/**
 * Generic hook for subscribing to a single table/filter
 * as per the Integration Guide.
 */
export function useRealtimeSubscription(
  table: string,
  filter: string,
  queryKey: string[] | readonly string[],
  event: 'INSERT' | 'UPDATE' | 'DELETE' | '*' = '*'
) {
  const queryClient = useQueryClient()
  const channelRef = useRef<RealtimeChannel | null>(null)

  useEffect(() => {
    const supabase = createClient()
    const channelName = `sub-${table}-${filter.replace(/[^a-zA-Z0-9]/g, '')}`

    const channel = supabase
      .channel(channelName)
      .on(
        'postgres_changes',
        { event, schema: 'public', table, filter },
        (payload) => {
          // console.debug(`[Realtime] ${event} on ${table}`, payload)
          queryClient.invalidateQueries({ queryKey })
        }
      )
      .subscribe()

    channelRef.current = channel

    return () => {
      if (channelRef.current) {
        supabase.removeChannel(channelRef.current)
        channelRef.current = null
      }
    }
  }, [table, filter, JSON.stringify(queryKey), event, queryClient])
}
