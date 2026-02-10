'use client'

import Link from 'next/link'
import { useState } from 'react'
import {
  Terminal,
  Bell,
  Search,
  Menu,
  X,
} from 'lucide-react'
import { ThemeToggle } from '@/components/shared/ThemeToggle'

/**
 * DashboardNavbar — Top navigation for all dashboard pages.
 * Includes search (light mode), notifications, and user avatar.
 */
export function DashboardNavbar() {
  const [mobileOpen, setMobileOpen] = useState(false)

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

          {/* User avatar */}
          <div
            className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-500 overflow-hidden border border-border cursor-pointer ring-2 ring-transparent hover:ring-cf-primary transition-all"
            aria-label="User profile"
          />

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
