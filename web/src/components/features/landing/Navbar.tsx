'use client'

import Link from 'next/link'
import { useState } from 'react'
import {
  Terminal,
  Compass,
  Menu,
  X,
} from 'lucide-react'
import { ThemeToggle } from '@/components/shared/ThemeToggle'

export function Navbar() {
  const [mobileOpen, setMobileOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border bg-background/80 backdrop-blur-md">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-3">
            {/* Dark mode: terminal icon | Light mode: compass icon */}
            <div className="flex size-8 items-center justify-center rounded bg-secondary border border-border text-cf-primary dark:text-cf-primary">
              <Terminal className="hidden dark:block size-5" />
              <Compass className="block dark:hidden size-5 text-foreground" />
            </div>
            <span className="text-lg font-bold tracking-tight text-foreground">
              <span className="hidden dark:inline">CodeForge AI</span>
              <span className="inline dark:hidden">CodeForge</span>
            </span>
          </Link>

          {/* Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-8">
            {/* Dark-mode links */}
            <Link
              href="/dashboard/builder"
              className="hidden dark:inline text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Builder
            </Link>
            <Link
              href="/dashboard/student"
              className="hidden dark:inline text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Student
            </Link>
            {/* Light-mode links */}
            <Link
              href="#features"
              className="inline dark:hidden text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Features
            </Link>
            {/* Shared links */}
            <Link
              href="#pricing"
              className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Pricing
            </Link>
            <Link
              href="#"
              className="inline dark:hidden text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
            >
              Docs
            </Link>
          </nav>

          {/* Right Actions */}
          <div className="flex items-center gap-4">
            <ThemeToggle />

            <Link
              href="/login"
              className="hidden sm:block text-sm font-medium text-foreground hover:text-cf-primary dark:hover:text-cf-primary transition-colors"
            >
              Sign In
            </Link>

            {/* Dark-mode CTA */}
            <Link
              href="/dashboard"
              className="hidden dark:flex h-9 items-center justify-center rounded-lg bg-foreground px-4 text-sm font-bold text-background hover:bg-foreground/90 transition-colors shadow-[0_0_15px_-3px_rgba(255,255,255,0.3)]"
            >
              Get Access
            </Link>

            {/* Light-mode CTA (sign-in button) */}
            <Link
              href="/login"
              className="flex dark:hidden h-9 items-center justify-center overflow-hidden rounded-sm border border-border px-4 bg-background hover:bg-muted text-foreground text-sm font-semibold transition-all"
            >
              Sign In
            </Link>

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
      </div>

      {/* Mobile dropdown */}
      {mobileOpen && (
        <div className="md:hidden border-t border-border bg-background px-4 py-4 space-y-3">
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
          <Link
            href="#pricing"
            className="block text-sm font-medium text-muted-foreground hover:text-foreground"
            onClick={() => setMobileOpen(false)}
          >
            Pricing
          </Link>
          <Link
            href="/login"
            className="block text-sm font-medium text-foreground"
            onClick={() => setMobileOpen(false)}
          >
            Sign In
          </Link>
        </div>
      )}
    </header>
  )
}
