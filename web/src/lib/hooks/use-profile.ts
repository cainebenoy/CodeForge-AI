'use client'

import {
  useQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query'
import { profileApi } from '@/lib/api'
import type { ProfileRead, ProfileCreate, ProfileUpdate } from '@/types/api.types'

// ── Query keys ──
export const profileKeys = {
  me: ['profile', 'me'] as const,
}

/**
 * Get the current user's profile.
 * Auto-creates the profile on the backend if it doesn't exist.
 */
export function useProfile() {
  return useQuery<ProfileRead>({
    queryKey: profileKeys.me,
    queryFn: () => profileApi.getMe(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1,
  })
}

/**
 * Create or upsert a profile (e.g., during onboarding).
 */
export function useCreateProfile() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: ProfileCreate) => profileApi.create(payload),
    onSuccess: (profile) => {
      queryClient.setQueryData(profileKeys.me, profile)
    },
  })
}

/**
 * Update the current user's profile.
 */
export function useUpdateProfile() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: ProfileUpdate) => profileApi.update(payload),
    onSuccess: (profile) => {
      queryClient.setQueryData(profileKeys.me, profile)
    },
  })
}
