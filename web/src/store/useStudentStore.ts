/**
 * Zustand store for Student Mode state
 */
import { create } from 'zustand'
import { devtools } from 'zustand/middleware'

interface StudentStore {
  // Current module and step
  currentModuleIndex: number
  currentStepIndex: number
  setCurrentModule: (index: number) => void
  setCurrentStep: (index: number) => void

  // Student's choices (for Choice Framework)
  choices: Record<string, string>
  setChoice: (decisionId: string, optionId: string) => void

  // Completed steps
  completedSteps: Set<string>
  markStepComplete: (stepId: string) => void
  isStepComplete: (stepId: string) => boolean
}

export const useStudentStore = create<StudentStore>()(
  devtools(
    (set, get) => ({
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
    { name: 'student-store' }
  )
)
