'use client'

import { useQuery, useQueryClient } from '@tanstack/react-query'
import { createClient } from '@/lib/supabase/client'
import { useRouter } from 'next/navigation'
import { useCallback } from 'react'
import type { User } from '@supabase/supabase-js'

/**
 * useUser — React Query hook for the current authenticated user.
 *
 * Returns the Supabase user object (id, email, user_metadata) along
 * with loading/error states. Also exposes signOut().
 *
 * Security: Uses supabase.auth.getUser() which validates the JWT
 * server-side, not just the cached session.
 */
export function useUser() {
  const router = useRouter()
  const queryClient = useQueryClient()
  const supabase = createClient()

  const query = useQuery<User | null>({
    queryKey: ['user'],
    queryFn: async () => {
      const { data: { user }, error } = await supabase.auth.getUser()
      if (error) throw error
      return user
    },
    staleTime: 5 * 60 * 1000, // 5 minutes — JWT won't change often
    retry: false, // Don't retry auth failures
  })

  const signOut = useCallback(async () => {
    await supabase.auth.signOut()
    queryClient.clear() // Clear all cached data on signout
    router.push('/login')
    router.refresh()
  }, [supabase, queryClient, router])

  return {
    user: query.data ?? null,
    isLoading: query.isLoading,
    error: query.error,
    signOut,
  }
}
