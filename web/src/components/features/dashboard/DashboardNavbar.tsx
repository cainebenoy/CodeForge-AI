'use client'

import Link from 'next/link'
import { useState, useRef, useEffect } from 'react'
import {
  Terminal,
  Bell,
  Search,
  Menu,
  X,
  LogOut,
  User,
  Settings,
} from 'lucide-react'
import { ThemeToggle } from '@/components/shared/ThemeToggle'
import { useUser } from '@/lib/hooks/use-user'

/**
 * DashboardNavbar — Top navigation for all dashboard pages.
 * Shows real user avatar/name from Supabase auth and provides sign-out.
 */
export function DashboardNavbar() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const menuRef = useRef<HTMLDivElement>(null)
  const { user, signOut } = useUser()

  // Close user menu on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false)
      }
    }
    if (userMenuOpen) document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [userMenuOpen])

  const avatarUrl = user?.user_metadata?.avatar_url as string | undefined
  const displayName =
    (user?.user_metadata?.full_name as string) ||
    (user?.user_metadata?.user_name as string) ||
    user?.email?.split('@')[0] ||
    'User'
  const initials = displayName.slice(0, 2).toUpperCase()

  return (
    <header className="flex-none sticky top-0 z-10 w-full border-b border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto max-w-7xl px-6 h-16 flex items-center justify-between">
        {/* Left: Logo + Nav */}
        <div className="flex items-center gap-10">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="h-8 w-8 flex items-center justify-center bg-cf-primary rounded-lg text-black">
              <Terminal className="size-5" />
            </div>
            <h1 className="text-lg font-bold tracking-tight text-foreground">
              CodeForge AI
            </h1>
          </Link>

          {/* Desktop nav links */}
          <nav className="hidden md:flex items-center gap-6">
            <Link
              href="/dashboard"
              className="text-sm font-medium text-foreground"
            >
              Dashboard
            </Link>
            <Link
              href="/dashboard/builder"
              className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Builder
            </Link>
            <Link
              href="/dashboard/student"
              className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Student
            </Link>
          </nav>
        </div>

        {/* Right: Search + Notifications + Avatar */}
        <div className="flex items-center gap-4">
          {/* Search (desktop) */}
          <div className="hidden md:flex items-center bg-muted rounded-lg px-3 py-1.5 w-64 focus-within:ring-2 focus-within:ring-cf-primary/50 transition-all">
            <Search className="size-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search projects..."
              className="bg-transparent border-none text-sm w-full focus:ring-0 text-foreground placeholder:text-muted-foreground ml-2 outline-none"
            />
          </div>

          <ThemeToggle />

          {/* Notifications */}
          <button
            className="relative p-2 text-muted-foreground hover:text-foreground transition-colors rounded-full hover:bg-muted"
            aria-label="Notifications"
          >
            <Bell className="size-5" />
            <span className="absolute top-2 right-2 h-2 w-2 rounded-full bg-red-500 border-2 border-background" />
          </button>

          {/* User avatar + dropdown */}
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="w-8 h-8 rounded-full overflow-hidden border border-border cursor-pointer ring-2 ring-transparent hover:ring-cf-primary transition-all"
              aria-label="User profile"
            >
              {avatarUrl ? (
                <img
                  src={avatarUrl}
                  alt={displayName}
                  className="w-full h-full object-cover"
                  referrerPolicy="no-referrer"
                />
              ) : (
                <div className="w-full h-full bg-gradient-to-tr from-blue-500 to-purple-500 flex items-center justify-center text-white text-xs font-bold">
                  {initials}
                </div>
              )}
            </button>

            {/* Dropdown */}
            {userMenuOpen && (
              <div className="absolute right-0 mt-2 w-56 rounded-lg border border-border bg-card shadow-xl py-1 z-50">
                <div className="px-4 py-3 border-b border-border">
                  <p className="text-sm font-medium text-foreground truncate">{displayName}</p>
                  {user?.email && (
                    <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                  )}
                </div>
                <Link
                  href="/dashboard"
                  className="flex items-center gap-2 px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                  onClick={() => setUserMenuOpen(false)}
                >
                  <User className="size-4" />
                  Profile
                </Link>
                <Link
                  href="/dashboard"
                  className="flex items-center gap-2 px-4 py-2 text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                  onClick={() => setUserMenuOpen(false)}
                >
                  <Settings className="size-4" />
                  Settings
                </Link>
                <div className="border-t border-border mt-1 pt-1">
                  <button
                    onClick={() => { setUserMenuOpen(false); signOut() }}
                    className="flex w-full items-center gap-2 px-4 py-2 text-sm text-red-500 hover:bg-red-500/10 transition-colors"
                  >
                    <LogOut className="size-4" />
                    Sign Out
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Mobile hamburger */}
          <button
            className="md:hidden p-2 text-muted-foreground hover:text-foreground"
            onClick={() => setMobileOpen(!mobileOpen)}
            aria-label="Toggle menu"
          >
            {mobileOpen ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>
        </div>
      </div>

      {/* Mobile dropdown */}
      {mobileOpen && (
        <div className="md:hidden border-t border-border bg-background px-6 py-4 space-y-3">
          <Link
            href="/dashboard"
            className="block text-sm font-medium text-foreground"
            onClick={() => setMobileOpen(false)}
          >
            Dashboard
          </Link>
          <Link
            href="/dashboard/builder"
            className="block text-sm font-medium text-muted-foreground hover:text-foreground"
            onClick={() => setMobileOpen(false)}
          >
            Builder
          </Link>
          <Link
            href="/dashboard/student"
            className="block text-sm font-medium text-muted-foreground hover:text-foreground"
            onClick={() => setMobileOpen(false)}
          >
            Student
          </Link>
          {/* Mobile search */}
          <div className="flex items-center bg-muted rounded-lg px-3 py-1.5 focus-within:ring-2 focus-within:ring-cf-primary/50 transition-all">
            <Search className="size-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search projects..."
              className="bg-transparent border-none text-sm w-full focus:ring-0 text-foreground placeholder:text-muted-foreground ml-2 outline-none"
            />
          </div>
        </div>
      )}
    </header>
  )
}
