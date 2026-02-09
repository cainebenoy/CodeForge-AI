import axios from 'axios'

const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

/**
 * API client instance with default config
 * Includes rate limiting and error handling
 */
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor for auth tokens
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('supabase.auth.token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 429) {
      // Rate limit exceeded
      const retryAfter = error.response.headers['retry-after']
      console.error(`Rate limit exceeded. Retry after ${retryAfter} seconds.`)
    }
    
    if (error.response?.status === 401) {
      // Unauthorized - redirect to login
      window.location.href = '/login'
    }

    return Promise.reject(error)
  }
)

/**
 * Agent API endpoints
 */
export const agentApi = {
  runAgent: async (projectId: string, agentType: string, context: any) => {
    const response = await apiClient.post('/v1/run-agent', {
      project_id: projectId,
      agent_type: agentType,
      input_context: context,
    })
    return response.data
  },

  getJobStatus: async (jobId: string) => {
    const response = await apiClient.get(`/v1/jobs/${jobId}`)
    return response.data
  },
}

/**
 * Project API endpoints
 */
export const projectApi = {
  getProject: async (projectId: string) => {
    const response = await apiClient.get(`/v1/projects/${projectId}`)
    return response.data
  },

  updateProject: async (projectId: string, data: any) => {
    const response = await apiClient.put(`/v1/projects/${projectId}`, data)
    return response.data
  },
}
