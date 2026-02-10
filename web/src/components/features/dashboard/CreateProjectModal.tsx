'use client'

import { useState } from 'react'
import { X, Loader2, Server, GraduationCap } from 'lucide-react'
import { useCreateProject } from '@/lib/hooks/use-project'
import { useRouter } from 'next/navigation'
import { toast } from '@/lib/hooks/use-toast'
import type { ProjectMode } from '@/types/api.types'

interface CreateProjectModalProps {
  open: boolean
  onClose: () => void
}

/**
 * CreateProjectModal — modal for creating a new project.
 *
 * Validates inputs client-side and calls the backend via useCreateProject().
 * On success, navigates to the new project page (builder or student).
 *
 * Security: title length capped at 100 chars, description at 500.
 */
export function CreateProjectModal({ open, onClose }: CreateProjectModalProps) {
  const router = useRouter()
  const createProject = useCreateProject()

  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [mode, setMode] = useState<ProjectMode>('builder')
  const [error, setError] = useState<string | null>(null)

  if (!open) return null

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    const trimmedTitle = title.trim()
    if (!trimmedTitle) {
      setError('Project title is required.')
      return
    }
    if (trimmedTitle.length > 100) {
      setError('Title cannot exceed 100 characters.')
      return
    }
    if (description.length > 500) {
      setError('Description cannot exceed 500 characters.')
      return
    }

    try {
      const project = await createProject.mutateAsync({
        title: trimmedTitle,
        description: description.trim() || undefined,
        mode,
      })

      // Navigate to the new project
      const basePath = mode === 'builder'
        ? `/dashboard/builder/${project.id}`
        : `/dashboard/student/${project.id}`
      router.push(basePath)
      toast.success('Project created', `"${trimmedTitle}" is ready.`)
      onClose()
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Failed to create project. Please try again.'
      setError(message)
    }
  }

  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) onClose()
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
      onClick={handleBackdropClick}
    >
      <div className="relative w-full max-w-lg mx-4 bg-card border border-border rounded-xl shadow-2xl">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border">
          <h2 className="text-lg font-bold text-foreground">Create New Project</h2>
          <button
            onClick={onClose}
            className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            aria-label="Close"
          >
            <X className="size-5" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 py-5 space-y-5">
          {/* Title */}
          <div>
            <label
              htmlFor="project-title"
              className="block text-sm font-medium text-foreground mb-1.5"
            >
              Project Name <span className="text-red-500">*</span>
            </label>
            <input
              id="project-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              maxLength={100}
              placeholder="My Awesome App"
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-cf-primary/50"
              autoFocus
            />
          </div>

          {/* Description */}
          <div>
            <label
              htmlFor="project-description"
              className="block text-sm font-medium text-foreground mb-1.5"
            >
              Description
            </label>
            <textarea
              id="project-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              maxLength={500}
              placeholder="A brief description of what you want to build or learn..."
              rows={3}
              className="w-full px-3 py-2 rounded-lg border border-border bg-background text-foreground text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-cf-primary/50 resize-none"
            />
            <p className="text-xs text-muted-foreground mt-1 text-right">
              {description.length}/500
            </p>
          </div>

          {/* Mode selection */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Mode
            </label>
            <div className="grid grid-cols-2 gap-3">
              <button
                type="button"
                onClick={() => setMode('builder')}
                className={`flex items-center gap-3 p-4 rounded-lg border-2 transition-all ${
                  mode === 'builder'
                    ? 'border-blue-500 bg-blue-500/5 ring-1 ring-blue-500/20'
                    : 'border-border hover:border-muted-foreground/30'
                }`}
              >
                <Server className={`size-5 ${mode === 'builder' ? 'text-blue-500' : 'text-muted-foreground'}`} />
                <div className="text-left">
                  <p className={`text-sm font-semibold ${mode === 'builder' ? 'text-blue-500' : 'text-foreground'}`}>
                    Builder
                  </p>
                  <p className="text-xs text-muted-foreground">AI builds your app</p>
                </div>
              </button>
              <button
                type="button"
                onClick={() => setMode('student')}
                className={`flex items-center gap-3 p-4 rounded-lg border-2 transition-all ${
                  mode === 'student'
                    ? 'border-violet-500 bg-violet-500/5 ring-1 ring-violet-500/20'
                    : 'border-border hover:border-muted-foreground/30'
                }`}
              >
                <GraduationCap className={`size-5 ${mode === 'student' ? 'text-violet-500' : 'text-muted-foreground'}`} />
                <div className="text-left">
                  <p className={`text-sm font-semibold ${mode === 'student' ? 'text-violet-500' : 'text-foreground'}`}>
                    Student
                  </p>
                  <p className="text-xs text-muted-foreground">AI teaches you</p>
                </div>
              </button>
            </div>
          </div>

          {/* Error */}
          {error && (
            <p className="text-sm text-red-500 bg-red-500/10 rounded-lg px-3 py-2">
              {error}
            </p>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg border border-border text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={createProject.isPending}
              className="flex items-center gap-2 px-5 py-2 rounded-lg bg-cf-primary text-black text-sm font-bold hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {createProject.isPending && <Loader2 className="size-4 animate-spin" />}
              Create Project
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
