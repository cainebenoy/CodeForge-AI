/**
 * Database types matching the Supabase schema.
 * Kept in sync with database/migrations/*.sql
 */

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export interface Database {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string
          username: string | null
          full_name: string | null
          avatar_url: string | null
          skill_level: 'beginner' | 'intermediate' | 'advanced' | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id: string
          username?: string | null
          full_name?: string | null
          avatar_url?: string | null
          skill_level?: 'beginner' | 'intermediate' | 'advanced' | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          username?: string | null
          full_name?: string | null
          avatar_url?: string | null
          skill_level?: 'beginner' | 'intermediate' | 'advanced' | null
          created_at?: string
          updated_at?: string
        }
      }
      projects: {
        Row: {
          id: string
          user_id: string
          title: string
          description: string | null
          mode: 'builder' | 'student'
          status: string
          requirements_spec: Json | null
          architecture_spec: Json | null
          tech_stack: string[] | null
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          title: string
          description?: string | null
          mode: 'builder' | 'student'
          status?: string
          requirements_spec?: Json | null
          architecture_spec?: Json | null
          tech_stack?: string[] | null
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          title?: string
          description?: string | null
          mode?: 'builder' | 'student'
          status?: string
          requirements_spec?: Json | null
          architecture_spec?: Json | null
          tech_stack?: string[] | null
          created_at?: string
          updated_at?: string
        }
      }
      project_files: {
        Row: {
          id: string
          project_id: string
          path: string
          content: string | null
          language: string | null
          version: number
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          project_id: string
          path: string
          content?: string | null
          language?: string | null
          version?: number
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          path?: string
          content?: string | null
          language?: string | null
          version?: number
          created_at?: string
          updated_at?: string
        }
      }
      agent_jobs: {
        Row: {
          id: string
          project_id: string
          user_id: string
          agent_type: string
          status: string
          progress: number
          result: Json | null
          error: string | null
          celery_task_id: string | null
          created_at: string
          started_at: string | null
          completed_at: string | null
        }
        Insert: {
          id?: string
          project_id: string
          user_id: string
          agent_type: string
          status?: string
          progress?: number
          result?: Json | null
          error?: string | null
          celery_task_id?: string | null
          created_at?: string
          started_at?: string | null
          completed_at?: string | null
        }
        Update: {
          id?: string
          project_id?: string
          user_id?: string
          agent_type?: string
          status?: string
          progress?: number
          result?: Json | null
          error?: string | null
          celery_task_id?: string | null
          started_at?: string | null
          completed_at?: string | null
        }
      }
      learning_roadmaps: {
        Row: {
          id: string
          project_id: string
          modules: Json
          current_step_index: number
          created_at: string
        }
        Insert: {
          id?: string
          project_id: string
          modules: Json
          current_step_index?: number
          created_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          modules?: Json
          current_step_index?: number
        }
      }
      daily_sessions: {
        Row: {
          id: string
          project_id: string
          transcript: Json | null
          concepts_covered: string[] | null
          duration_minutes: number
          created_at: string
        }
        Insert: {
          id?: string
          project_id: string
          transcript?: Json | null
          concepts_covered?: string[] | null
          duration_minutes?: number
          created_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          transcript?: Json | null
          concepts_covered?: string[] | null
          duration_minutes?: number
        }
      }
    }
  }
}
