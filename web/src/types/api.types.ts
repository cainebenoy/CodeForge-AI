/**
 * API Types — TypeScript mirrors of backend Pydantic schemas.
 *
 * These types define the contract between frontend and FastAPI backend.
 * All request bodies use `extra="forbid"` on the backend — unknown fields
 * will cause 422 errors. Keep these in sync with app/schemas/protocol.py.
 */

// ═══════════════════════════════════════════
// ENUMS
// ═══════════════════════════════════════════

export type AgentType = 'research' | 'wireframe' | 'code' | 'qa' | 'pedagogy' | 'roadmap'

export type JobStatusType =
  | 'queued'
  | 'running'
  | 'completed'
  | 'failed'
  | 'waiting_for_input'
  | 'cancelled'

export type ProjectMode = 'builder' | 'student'

export type ProjectStatus = 'planning' | 'in-progress' | 'building' | 'completed' | 'archived'

export type SkillLevel = 'beginner' | 'intermediate' | 'advanced'

export type QAIssueSeverity = 'critical' | 'high' | 'medium' | 'low'

export type PriorityLevel = 'must-have' | 'should-have' | 'nice-to-have'

// ═══════════════════════════════════════════
// REQUEST SCHEMAS (frontend → backend)
// ═══════════════════════════════════════════

export interface AgentRequest {
  project_id: string
  agent_type: AgentType
  input_context?: Record<string, unknown>
}

export interface ProjectCreate {
  title: string
  description?: string
  mode: ProjectMode
  tech_stack?: string[]
}

export interface ProjectUpdate {
  title?: string
  description?: string
  status?: ProjectStatus
}

export interface CodeFileCreate {
  path: string
  content: string
  language: string
}

export interface CodeFileUpdate {
  content: string
  language?: string
}

export interface ProfileCreate {
  username?: string
  full_name?: string
  avatar_url?: string
  skill_level?: SkillLevel
}

export interface ProfileUpdate {
  username?: string
  full_name?: string
  avatar_url?: string
  skill_level?: SkillLevel
}

export interface RoadmapCreate {
  skill_level: SkillLevel
  focus_areas?: string[]
}

export interface RoadmapProgressUpdate {
  step_index: number
}

export interface SessionCreate {
  transcript: Array<{ role: string; content: string }>
  concepts_covered: string[]
  duration_minutes: number
}

export interface ChoiceFrameworkRequest {
  decision_context: string
  module_index: number
}

export interface ChoiceSelection {
  module_index: number
  option_id: string
}

export interface ClarificationAnswer {
  answers: Array<Record<string, string>>
}

export interface RefactorRequest {
  selected_code: string
  instruction: string
}

export interface GitHubExportRequest {
  repo_name: string
  description?: string
  private: boolean
  github_token: string
}

// ═══════════════════════════════════════════
// RESPONSE SCHEMAS (backend → frontend)
// ═══════════════════════════════════════════

export interface AgentResponse {
  job_id: string
  status: JobStatusType
  estimated_time?: number
}

export interface JobStatus {
  job_id: string
  status: JobStatusType
  agent_type: AgentType
  project_id: string
  result?: Record<string, unknown> | null
  error?: string | null
  progress: number
  created_at: string
  completed_at?: string | null
}

export interface PaginatedResponse<T = unknown> {
  items: T[]
  total: number
  page: number
  page_size: number
  has_more: boolean
}

export interface ProfileRead {
  id: string
  username?: string | null
  full_name?: string | null
  avatar_url?: string | null
  skill_level?: SkillLevel | null
  created_at?: string | null
  updated_at?: string | null
}

export interface StudentProgress {
  roadmap_id: string
  project_id: string
  completed_modules: number
  total_modules: number
  current_module?: number | null
  percent_complete: number
  total_sessions: number
  total_time_minutes: number
}

// ── Project (as returned by API) ──
export interface Project {
  id: string
  user_id: string
  title: string
  description: string | null
  mode: ProjectMode
  status: ProjectStatus
  requirements_spec: Record<string, unknown> | null
  architecture_spec: Record<string, unknown> | null
  tech_stack: string[] | null
  created_at: string
  updated_at: string
}

// ── Code File (as returned by API) ──
export interface CodeFile {
  id: string
  project_id: string
  path: string
  content: string | null
  language: string | null
  version: number
  created_at: string
  updated_at: string
}

// ═══════════════════════════════════════════
// AGENT OUTPUT SCHEMAS
// ═══════════════════════════════════════════

export interface UserPersona {
  name: string
  description: string
  pain_points: string[]
}

export interface Feature {
  name: string
  description: string
  priority: PriorityLevel
  user_stories: string[]
}

export interface RequirementsDoc {
  app_name: string
  elevator_pitch: string
  target_audience: UserPersona[]
  core_features: Feature[]
  recommended_stack: Record<string, string>
  technical_constraints?: string[]
}

export interface PageComponent {
  name: string
  type: string
  props: string[]
  children?: PageComponent[]
}

export interface PageRoute {
  path: string
  name: string
  components: PageComponent[]
  layout?: string
}

export interface WireframeSpec {
  site_map: PageRoute[]
  global_state_needs: string[]
  theme_colors: Record<string, string>
}

export interface GeneratedFile {
  path: string
  content: string
  language: string
  description?: string
}

export interface CodeGenerationResult {
  files: GeneratedFile[]
  summary: string
  dependencies: Record<string, string>
}

export interface QAIssue {
  file: string
  line?: number
  severity: QAIssueSeverity
  message: string
  suggestion?: string
}

export interface QAResult {
  passed: boolean
  issues: QAIssue[]
  summary: string
  score: number
}

export interface LearningStep {
  title: string
  description: string
  estimated_minutes?: number
}

export interface PedagogyResponse {
  encouragement: string
  steps: LearningStep[]
  key_concept: string
  further_exploration: string[]
}

export interface LearningModule {
  title: string
  description: string
  objectives: string[]
  steps: LearningStep[]
  estimated_hours: number
  prerequisites?: string[]
}

export interface LearningRoadmap {
  modules: LearningModule[]
  total_estimated_hours: number
  prerequisites: string[]
  learning_objectives: string[]
}

export interface ImplementationOption {
  id: string
  title: string
  description: string
  difficulty: SkillLevel
  pros: string[]
  cons: string[]
  estimated_time: string
}

export interface ChoiceFramework {
  context: string
  options: ImplementationOption[]
  recommendation?: string
}

export interface ClarificationQuestion {
  question: string
  context?: string
  options?: string[]
}

export interface ClarificationResponse {
  questions: ClarificationQuestion[]
  is_complete: boolean
}

export interface RefactorResult {
  original_code: string
  refactored_code: string
  explanation: string
  full_file_content: string
}

// ═══════════════════════════════════════════
// SSE EVENT TYPES
// ═══════════════════════════════════════════

export interface SSEProgressEvent {
  progress: number
  status: JobStatusType
  message?: string
}

export interface SSECompleteEvent {
  result: Record<string, unknown>
  status: 'completed'
}

export interface SSEErrorEvent {
  error: string
  status: 'failed'
}

export interface SSEWaitingEvent {
  questions: ClarificationQuestion[]
  status: 'waiting_for_input'
}

export type SSEEvent = SSEProgressEvent | SSECompleteEvent | SSEErrorEvent | SSEWaitingEvent

export interface ChatMessage {
  id: string
  project_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  is_thinking: boolean
  created_at: string
  metadata?: Record<string, unknown>
}

