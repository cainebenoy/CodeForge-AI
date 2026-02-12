import axios from 'axios'
import { createClient } from '@/lib/supabase/client'
import type {
  AgentRequest,
  AgentResponse,
  JobStatus,
  Project,
  ProjectCreate,
  ProjectUpdate,
  CodeFile,
  CodeFileCreate,
  CodeFileUpdate,
  PaginatedResponse,
  ProfileRead,
  ProfileCreate,
  ProfileUpdate,
  RoadmapCreate,
  RoadmapProgressUpdate,
  SessionCreate,
  ChoiceFrameworkRequest,
  ChoiceFramework,
  ChoiceSelection,
  StudentProgress,
  ClarificationAnswer,
  RefactorRequest,
  RefactorResult,
  GitHubExportRequest,
} from '@/types/api.types'

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

/**
 * Axios client configured for the FastAPI backend.
 *
 * Security:
 * - Auth token injected from Supabase session (not localStorage)
 * - CSRF bypassed on backend when using Bearer tokens
 * - 401 redirects handled via response interceptor
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60_000, // 60s — agent calls can be slow
  headers: { 'Content-Type': 'application/json' },
})

// ── Request interceptor: inject Supabase JWT ──
apiClient.interceptors.request.use(
  async (config) => {
    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()
      if (session?.access_token) {
        config.headers.Authorization = `Bearer ${session.access_token}`
        config.headers['X-User-ID'] = session.user.id
      }
    } catch {
      // If Supabase client fails (SSR), skip token
    }
    return config
  },
  (error) => Promise.reject(error),
)

// ── Response interceptor: handle 401 + 429 ──
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers['retry-after']
      console.error(`Rate limited. Retry after ${retryAfter}s`)
    }
    if (error.response?.status === 401) {
      // Log the error but don't auto-redirect to prevent loops
      // Let the UI components handle authentication errors gracefully
      console.error('Unauthorized request - profile may not exist yet')
    }
    return Promise.reject(error)
  },
)

// ═══════════════════════════════════════════
// PROJECT API
// ═══════════════════════════════════════════

export const projectApi = {
  /** List the current user's projects (paginated, filterable) */
  list: async (params?: {
    page?: number
    page_size?: number
    mode?: string
    status?: string
  }): Promise<PaginatedResponse<Project>> => {
    const { data } = await apiClient.get('/v1/projects/', { params })
    return data
  },

  /** Get a single project by ID */
  get: async (projectId: string): Promise<Project> => {
    const { data } = await apiClient.get(`/v1/projects/${projectId}`)
    return data
  },

  /** Create a new project */
  create: async (payload: ProjectCreate): Promise<Project> => {
    const { data } = await apiClient.post('/v1/projects/', payload)
    return data
  },

  /** Update a project */
  update: async (projectId: string, payload: ProjectUpdate): Promise<Project> => {
    const { data } = await apiClient.put(`/v1/projects/${projectId}`, payload)
    return data
  },

  /** Delete (archive) a project */
  delete: async (projectId: string): Promise<void> => {
    await apiClient.delete(`/v1/projects/${projectId}`)
  },

  /** List all files for a project */
  listFiles: async (projectId: string): Promise<{ project_id: string; count: number; files: CodeFile[] }> => {
    const { data } = await apiClient.get(`/v1/projects/${projectId}/files`)
    return data
  },

  /** Get a single file by path */
  getFile: async (projectId: string, filePath: string): Promise<CodeFile> => {
    const { data } = await apiClient.get(`/v1/projects/${projectId}/files/${filePath}`)
    return data
  },

  /** Create or upsert a file */
  createFile: async (projectId: string, payload: CodeFileCreate): Promise<CodeFile> => {
    const { data } = await apiClient.post(`/v1/projects/${projectId}/files`, payload)
    return data
  },

  /** Update a file's content */
  updateFile: async (projectId: string, filePath: string, payload: CodeFileUpdate): Promise<CodeFile> => {
    const { data } = await apiClient.put(`/v1/projects/${projectId}/files/${filePath}`, payload)
    return data
  },

  /** Delete a file */
  deleteFile: async (projectId: string, filePath: string): Promise<void> => {
    await apiClient.delete(`/v1/projects/${projectId}/files/${filePath}`)
  },

  /** AI-refactor a code segment */
  refactorFile: async (
    projectId: string,
    filePath: string,
    payload: RefactorRequest,
    apply?: boolean,
  ): Promise<RefactorResult> => {
    const { data } = await apiClient.post(
      `/v1/projects/${projectId}/files/${filePath}/refactor`,
      payload,
      { params: apply !== undefined ? { apply } : undefined },
    )
    return data
  },

  /** Export project to GitHub */
  exportToGitHub: async (projectId: string, payload: GitHubExportRequest) => {
    const { data } = await apiClient.post(`/v1/projects/${projectId}/export/github`, payload)
    return data
  },
}

// ═══════════════════════════════════════════
// AGENT API
// ═══════════════════════════════════════════

export const agentApi = {
  /** Trigger a single agent */
  runAgent: async (payload: AgentRequest): Promise<AgentResponse> => {
    const { data } = await apiClient.post('/v1/agents/run-agent', payload)
    return data
  },

  /** Trigger the full builder pipeline (research→wireframe→code→qa) */
  runPipeline: async (payload: AgentRequest): Promise<AgentResponse> => {
    const { data } = await apiClient.post('/v1/agents/run-pipeline', payload)
    return data
  },

  /** Get the status of a job */
  getJobStatus: async (jobId: string): Promise<JobStatus> => {
    const { data } = await apiClient.get(`/v1/agents/jobs/${jobId}`)
    return data
  },

  /** List jobs for a project (paginated) */
  listJobs: async (projectId: string, params?: { page?: number; page_size?: number }): Promise<PaginatedResponse<JobStatus>> => {
    const { data } = await apiClient.get(`/v1/agents/jobs/${projectId}/list`, { params })
    return data
  },

  /** Respond to agent clarification questions */
  respondToAgent: async (jobId: string, payload: ClarificationAnswer): Promise<AgentResponse> => {
    const { data } = await apiClient.post(`/v1/agents/jobs/${jobId}/respond`, payload)
    return data
  },

  /** Cancel a running/queued job */
  cancelJob: async (jobId: string): Promise<{ job_id: string; status: string; message: string }> => {
    const { data } = await apiClient.post(`/v1/agents/jobs/${jobId}/cancel`)
    return data
  },

  /**
   * Get the SSE stream URL for a job.
   * Use with EventSource, not axios — returns the URL string, not data.
   */
  getStreamUrl: (jobId: string): string => {
    return `${API_BASE_URL}/v1/agents/jobs/${jobId}/stream`
  },
}

// ═══════════════════════════════════════════
// PROFILE API
// ═══════════════════════════════════════════

export const profileApi = {
  /** Get the current user's profile (auto-creates if missing) */
  getMe: async (): Promise<ProfileRead> => {
    const { data } = await apiClient.get('/v1/profiles/me')
    return data
  },

  /** Create/upsert a profile */
  create: async (payload: ProfileCreate): Promise<ProfileRead> => {
    const { data } = await apiClient.post('/v1/profiles/', payload)
    return data
  },

  /** Update the current user's profile */
  update: async (payload: ProfileUpdate): Promise<ProfileRead> => {
    const { data } = await apiClient.put('/v1/profiles/me', payload)
    return data
  },
}

// ═══════════════════════════════════════════
// STUDENT API
// ═══════════════════════════════════════════

export const studentApi = {
  /** Generate a learning roadmap */
  createRoadmap: async (projectId: string, payload: RoadmapCreate) => {
    const { data } = await apiClient.post(`/v1/student/${projectId}/roadmap`, payload)
    return data
  },

  /** Get existing roadmap */
  getRoadmap: async (projectId: string) => {
    const { data } = await apiClient.get(`/v1/student/${projectId}/roadmap`)
    return data
  },

  /** Update roadmap progress */
  updateProgress: async (projectId: string, payload: RoadmapProgressUpdate) => {
    const { data } = await apiClient.put(`/v1/student/${projectId}/roadmap/progress`, payload)
    return data
  },

  /** Record a study session */
  createSession: async (projectId: string, payload: SessionCreate) => {
    const { data } = await apiClient.post(`/v1/student/${projectId}/sessions`, payload)
    return data
  },

  /** List sessions */
  listSessions: async (projectId: string, limit?: number) => {
    const { data } = await apiClient.get(`/v1/student/${projectId}/sessions`, {
      params: limit ? { limit } : undefined,
    })
    return data
  },

  /** Generate choice framework options */
  getChoiceFramework: async (projectId: string, payload: ChoiceFrameworkRequest): Promise<ChoiceFramework> => {
    const { data } = await apiClient.post(`/v1/student/${projectId}/choice`, payload)
    return data
  },

  /** Save student's choice selection */
  selectChoice: async (projectId: string, payload: ChoiceSelection) => {
    const { data } = await apiClient.put(`/v1/student/${projectId}/choice`, payload)
    return data
  },

  /** Get computed student progress */
  getProgress: async (projectId: string): Promise<StudentProgress> => {
    const { data } = await apiClient.get(`/v1/student/${projectId}/progress`)
    return data
  },
}
