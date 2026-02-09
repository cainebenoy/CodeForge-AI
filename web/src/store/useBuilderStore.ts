/**
 * Zustand store for Builder Mode state
 */
import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

type AgentType = 'research' | 'wireframe' | 'code' | 'qa'

interface BuilderStore {
  // Active file in editor
  activeFile: string | null
  setActiveFile: (path: string | null) => void

  // Sidebar state
  isSidebarOpen: boolean
  toggleSidebar: () => void

  // Current active agent
  activeAgent: AgentType | null
  setActiveAgent: (agent: AgentType | null) => void

  // Generated files (virtual file system)
  generatedFiles: Record<string, string>
  addFile: (path: string, content: string) => void
  updateFile: (path: string, content: string) => void
  removeFile: (path: string) => void
  clearFiles: () => void
}

export const useBuilderStore = create<BuilderStore>()(
  devtools(
    (set) => ({
      activeFile: null,
      setActiveFile: (path) => set({ activeFile: path }),

      isSidebarOpen: true,
      toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),

      activeAgent: null,
      setActiveAgent: (agent) => set({ activeAgent: agent }),

      generatedFiles: {},
      addFile: (path, content) =>
        set((state) => ({
          generatedFiles: { ...state.generatedFiles, [path]: content },
        })),
      updateFile: (path, content) =>
        set((state) => ({
          generatedFiles: { ...state.generatedFiles, [path]: content },
        })),
      removeFile: (path) =>
        set((state) => {
          const { [path]: _, ...rest } = state.generatedFiles
          return { generatedFiles: rest }
        }),
      clearFiles: () => set({ generatedFiles: {} }),
    }),
    { name: 'builder-store' }
  )
)
