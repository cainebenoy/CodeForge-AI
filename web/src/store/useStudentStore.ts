/**
 * Zustand store for Student Mode state
 */
import { create } from 'zustand'
import { devtools, persist } from 'zustand/middleware'

interface StudentStore {
  // Active student project (persisted for curriculum page)
  activeProjectId: string | null
  setActiveProjectId: (id: string | null) => void

  // Current module and step
  currentModuleIndex: number
  currentStepIndex: number
  setCurrentModule: (index: number) => void
  setCurrentStep: (index: number) => void

  // Student's choices (for Choice Framework)
  choices: Record<string, string>
  setChoice: (decisionId: string, optionId: string) => void

  // Completed steps (serialized as array for persist)
  completedSteps: Set<string>
  markStepComplete: (stepId: string) => void
  isStepComplete: (stepId: string) => boolean
}

export const useStudentStore = create<StudentStore>()(
  devtools(
    persist(
      (set, get) => ({
        activeProjectId: null,
        setActiveProjectId: (id) => set({ activeProjectId: id }),

        currentModuleIndex: 0,
        currentStepIndex: 0,
        setCurrentModule: (index) => set({ currentModuleIndex: index }),
        setCurrentStep: (index) => set({ currentStepIndex: index }),

        choices: {},
        setChoice: (decisionId, optionId) =>
          set((state) => ({
            choices: { ...state.choices, [decisionId]: optionId },
          })),

        completedSteps: new Set(),
        markStepComplete: (stepId) =>
          set((state) => ({
            completedSteps: new Set(state.completedSteps).add(stepId),
          })),
        isStepComplete: (stepId) => get().completedSteps.has(stepId),
      }),
      {
        name: 'student-store',
        // Custom storage to handle Set serialization
        partialize: (state) => ({
          activeProjectId: state.activeProjectId,
          currentModuleIndex: state.currentModuleIndex,
          currentStepIndex: state.currentStepIndex,
          choices: state.choices,
          completedSteps: Array.from(state.completedSteps),
        }),
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        merge: (persisted: any, current) => ({
          ...current,
          ...(persisted as Partial<StudentStore>),
          completedSteps: new Set(persisted?.completedSteps ?? []),
        }),
      },
    ),
    { name: 'student-store' },
  ),
)
