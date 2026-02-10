'use client'

import { useState } from 'react'
import { createClient } from '@/lib/supabase/client'
import { Code2, Github, Loader2, AlertCircle } from 'lucide-react'
import { useSearchParams } from 'next/navigation'

/**
 * Login page — GitHub OAuth via Supabase Auth.
 *
 * Dark: Zinc-950 centered card with GitHub button, code-themed.
 * Light: White card with subtle shadow, clean design.
 *
 * Security: OAuth redirect uses server-side callback (/auth/callback)
 * which exchanges code for session via cookie-based auth.
 */
export default function LoginPage() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const searchParams = useSearchParams()
  const authError = searchParams.get('error')
  const redirect = searchParams.get('redirect')

  const handleGitHubLogin = async () => {
    setLoading(true)
    setError(null)

    try {
      const supabase = createClient()
      const { error } = await supabase.auth.signInWithOAuth({
        provider: 'github',
        options: {
          redirectTo: `${window.location.origin}/auth/callback${redirect ? `?next=${redirect}` : ''}`,
        },
      })

      if (error) {
        setError(error.message)
        setLoading(false)
      }
      // If no error, Supabase redirects to GitHub — page will unload
    } catch {
      setError('An unexpected error occurred. Please try again.')
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col items-center gap-8">
      {/* Logo */}
      <div className="flex items-center gap-3">
        <Code2 className="size-10 dark:text-cf-primary text-violet-600" />
        <h1 className="text-3xl font-bold tracking-tight text-foreground">
          CodeForge<span className="dark:text-cf-primary text-violet-600"> AI</span>
        </h1>
      </div>

      {/* Card */}
      <div
        className="w-full max-w-sm rounded-lg border p-8 shadow-lg
                    dark:border-zinc-800 dark:bg-zinc-900
                    border-border bg-white"
      >
        <div className="mb-6 text-center">
          <h2 className="text-xl font-bold text-foreground mb-1">Welcome back</h2>
          <p className="text-sm text-muted-foreground">
            Sign in to continue building with your AI engineering team.
          </p>
        </div>

        {/* Error messages */}
        {(error || authError) && (
          <div className="mb-4 flex items-start gap-2 rounded-md border border-red-200 bg-red-50 p-3 dark:border-red-800 dark:bg-red-900/20">
            <AlertCircle className="size-4 text-red-600 dark:text-red-400 mt-0.5 shrink-0" />
            <p className="text-sm text-red-600 dark:text-red-400">
              {error || 'Authentication failed. Please try again.'}
            </p>
          </div>
        )}

        {/* GitHub OAuth button */}
        <button
          onClick={handleGitHubLogin}
          disabled={loading}
          className="flex w-full items-center justify-center gap-3 rounded-md px-4 py-3
                     font-semibold text-sm transition-all
                     dark:bg-white dark:text-black dark:hover:bg-zinc-200
                     bg-zinc-900 text-white hover:bg-zinc-800
                     disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <Loader2 className="size-5 animate-spin" />
          ) : (
            <Github className="size-5" />
          )}
          {loading ? 'Redirecting to GitHub...' : 'Continue with GitHub'}
        </button>

        <p className="mt-4 text-center text-xs text-muted-foreground">
          By signing in, you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>

      {/* Back to landing */}
      <a
        href="/"
        className="text-sm text-muted-foreground hover:text-foreground transition-colors"
      >
        ← Back to home
      </a>
    </div>
  )
}
