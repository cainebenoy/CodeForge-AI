# CodeForge AI — Detailed App Flow & User Journey

**Document Purpose:** This file maps the specific UI states, user actions, and system responses for the CodeForge platform. It serves as the blueprint for frontend development (Next.js) and Agent orchestration.

## 1. Global Onboarding Flow

**Goal:** Route users to the correct mode ("Build" vs. "Learn") immediately.

### 1.1 Landing Page

- **Hero Section:** "Your AI Engineering Team" (Headline).
- **Primary CTA:** "Start Building" (Direct to Builder Mode).
- **Secondary CTA:** "Start Learning" (Direct to Student Mode).

### 1.2 Authentication (Supabase Auth)

- **Provider:** GitHub (preferred for devs) or Email/Password.
- **Post-Auth Redirect:**
    - *New User:* Onboarding Questionnaire.
    - *Returning User:* Dashboard.

### 1.3 New User Onboarding

- **Question:** "What is your primary goal?"
    - [Option A] "I have an idea I need to ship ASAP." -> **Sets `default_mode = 'builder'`**
    - [Option B] "I want to learn how to build professional apps." -> **Sets `default_mode = 'student'`**

## 2. Builder Mode Workflow (The "Production" Path)

**Goal:** From idea to GitHub repository with minimal friction.

### Step 1: The Brief (Input)

- **UI State:** Clean, distraction-free form (similar to Typeform or Perplexity).
- **Input Fields:**
    1. **Project Name:** (e.g., "DogWalker CRM")
    2. **One-Liner:** (e.g., "A CRM for dog walkers to manage clients and schedules.")
    3. **Target Audience:** (e.g., "Freelance dog walkers.")
    4. **Tech Stack Preferences:** (Tags: Next.js, Supabase, Tailwind).
- **Action:** User clicks "Hire Team" (Submit).
- **System Response:** Transition to "War Room" loading state.

### Step 2: Research & Spec Generation

- **Agent:** Research Agent.
- **UI State:** Split View.
    - *Left Panel:* Chat Interface (Agent asking clarifying questions).
    - *Right Panel:* Live Document (`requirements.md`) rendering in real-time.
- **Interaction Loop:**
    1. Agent: "Should the CRM handle payments, or just scheduling?"
    2. User: "Just scheduling for MVP."
    3. System: Updates `requirements.md` to remove Stripe integration.
- **Exit Condition:** User clicks "Approve Spec."

### Step 3: Wireframe & Architecture

- **Agent:** Wireframe Agent.
- **UI State:** Tree Visualization (React Flow or simple nested list).
- **Visuals:**
    - **Site Map:** `Home -> Dashboard -> Settings`.
    - **Component Tree:** `Dashboard -> [StatCard, ClientTable, Calendar]`.
    - **Schema Preview:** Shows table relationships (e.g., `User` 1:N `Dogs`).
- **Action:** User clicks "Confirm Architecture."

### Step 4: The Build (Code Generation)

- **Agent:** Code Agent.
- **UI State:** IDE Simulation (Monaco Editor).
    - *Sidebar:* File tree populating dynamically.
    - *Editor:* Streams code generation line-by-line (for transparency).
    - *Terminal:* Mock terminal showing "Installing packages...", "Linting...".
- **User Control:** User can pause generation or click a file to see it being written.

### Step 5: QA & Export

- **Agent:** QA Agent.
- **UI State:** Dashboard View.
- **Outputs:**
    - **Repo Link:** "Open in GitHub" (Repository created via API).
    - **Deployment:** "Deploy to Vercel" button.
    - **QA Report:** List of potential "TODOs" or "Optimizations" the AI couldn't finish (e.g., "Add API keys to .env").

## 3. Student Mode Workflow (The "Learning" Path)

**Goal:** Teach engineering decision-making through a guided project.

### Step 1: Skill Assessment

- **UI:** Chat-based Adaptive Quiz.
- **Flow:**
    1. System: "Have you used React before?" (Yes/No).
    2. System: "If you wanted to pass data from a parent to a child, what would you use?" (Multiple Choice: Props, Context, Redux).
- **Output:** Sets `skill_level` (Beginner/Intermediate/Advanced) in User Profile.

### Step 2: Project Selection

- **UI:** Card Grid.
- **Content:**
    - *Beginner:* "To-Do List" (Focus: State).
    - *Intermediate:* "Trello Clone" (Focus: Drag-n-Drop, DB).
    - *Advanced:* "Real-time Chat" (Focus: Sockets, Auth).
- **Selection:** User picks "Trello Clone".

### Step 3: Roadmap Generation

- **UI:** Kanban Board (Modules).
- **Example Roadmap:**
    - [Unlocked] Module 1: Project Setup & Tailwind.
    - [Locked] Module 2: Database Schema (Supabase).
    - [Locked] Module 3: Drag and Drop Logic.

### Step 4: The Daily Session (Core Interaction)

- **UI:** Split Screen IDE.
    - *Left:* Mentor Chat (Pedagogy Agent).
    - *Right:* Code Editor (Sandboxed).
- **Interaction:**
    1. **Objective:** Mentor sets the goal ("Today, let's build the columns").
    2. **Guidance:** Mentor provides *hints*, not code. "How would you structure a column visually?"
    3. **Validation:** User writes code. Mentor runs a "Check" in the background.
    4. **Correction:** If user fails, Mentor explains *why* (e.g., "You forgot the `key` prop in the map function").

### Step 5: The "Choice Framework" Moment (Key Feature)

- **Trigger:** User reaches a major architectural decision node (e.g., "How do we store the cards?").
- **UI State:** **Modal Overlay / Focus Mode**.
- **The Cards:** Three distinct options appear.
    - **Option A (The Simple Way):** "Local Storage."
        - *Pros:* Fast, no backend.
        - *Cons:* Data lost on refresh/device change.
    - **Option B (The Standard Way):** "PostgreSQL (Supabase)."
        - *Pros:* Persistent, scalable.
        - *Cons:* Async complexity.
    - **Option C (The 'Hard' Way):** "Custom JSON File Server."
        - *Pros:* Learn file I/O.
        - *Cons:* Slow, manual parsing.
- **Selection:** User clicks "Option B".
- **Outcome:** The Pedagogy Agent generates the *rest of the tutorial steps* dynamically based on Supabase.

### Step 6: Review & Certification

- **Trigger:** Project Completion.
- **UI:** "Code Review" Report.
- **Content:**
    - "You used `useEffect` correctly 90% of the time."
    - "Security Warning: You committed API keys (simulated)."
- **Reward:** "Project Badge" added to User Profile.

## 4. Shared UI Elements & States

### 4.1 The "Thinking" State

- **Context:** Used in both modes when Agents are processing.
- **Visual:** Not a spinner. A text log showing "Thought Steps."
    - *Example:* "Reading requirements... Checking Supabase docs... Generating schema..."
- **Purpose:** Builds trust and explains *how* the AI is working.

### 4.2 The "Revision" Request

- **Context:** User wants to change something.
- **Interaction:**
    - User highlights text (Builder Mode) or code (Student Mode).
    - Context menu appears: "Refine with AI."
    - Input box: "Make this more accessible."

## 5. Edge Cases & Error Handling

- **API Failure:** If LLM times out.
    - *UI:* "Brain Freeze. Retrying..." (Auto-retry logic).
    - *Fallback:* Button to "Manually Retry".
- **Ambiguous Requirements:**
    - *Behavior:* Research Agent pauses and *demands* clarification before proceeding. It does not guess blindly.
- **Code Syntax Errors:**
    - *Behavior:* QA Agent runs a linter pass *before* showing code to user. If syntax is invalid, it auto-regenerates.