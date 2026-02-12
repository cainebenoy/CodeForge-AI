'use client'

import { DashboardNavbar } from '@/components/features/dashboard/DashboardNavbar'
import { useProfile } from '@/lib/hooks/use-profile'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  // Auto-create profile if it doesn't exist
  // This ensures the backend has a user record before any other API calls
  const { data: profile, isLoading, error } = useProfile()

  // Wait for profile to load before rendering children
  // This prevents child components from making API calls before profile exists
  if (isLoading) {
    return (
      <div className="flex min-h-screen flex-col bg-background text-foreground">
        <DashboardNavbar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-muted-foreground">Loading...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex min-h-screen flex-col bg-background text-foreground">
        <DashboardNavbar />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-destructive">Failed to load profile. Please try refreshing.</div>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col bg-background text-foreground">
      <DashboardNavbar />
      <div className="flex-1">{children}</div>
    </div>
  )
}

