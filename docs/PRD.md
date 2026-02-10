# CodeForge AI — Product Requirements Document (PRD)

**Document Purpose:** Define the product vision, target users, core features, and success metrics for CodeForge AI. This document drives all design and engineering decisions.

## 1. Product Vision

**CodeForge AI** is an AI-powered engineering platform that transforms ideas into production-ready applications. It operates in two modes:

- **Builder Mode:** For entrepreneurs and developers who want to ship fast — AI researches, designs, codes, and QA-reviews applications from a one-liner description.
- **Student Mode:** For learners who want to understand _how_ to build — AI mentors through guided, project-based learning with decision frameworks.

**One-Liner:** "Your AI Engineering Team — from idea to GitHub repo, or from beginner to builder."

## 2. Target Users

### Builder Mode

| Persona                 | Description                                 | Goal                                          |
| ----------------------- | ------------------------------------------- | --------------------------------------------- |
| **Indie Hacker**        | Solo founder with an idea, limited time     | Ship MVP in hours, not weeks                  |
| **Freelance Developer** | Needs rapid prototyping for client projects | Generate boilerplate and architecture quickly |
| **Product Manager**     | Non-technical, needs to validate concepts   | Get a working prototype to test with users    |

### Student Mode

| Persona                      | Description                                           | Goal                                     |
| ---------------------------- | ----------------------------------------------------- | ---------------------------------------- |
| **Coding Bootcamp Graduate** | Has syntax knowledge, lacks architecture intuition    | Learn to make engineering decisions      |
| **Self-Taught Developer**    | Learned from tutorials, wants real project experience | Build something meaningful with guidance |
| **CS Student**               | Academic knowledge, needs practical skills            | Bridge theory-to-practice gap            |

## 3. Core Features

### 3.1 Builder Mode Features

| Feature              | Priority     | Description                                                              | Status       |
| -------------------- | ------------ | ------------------------------------------------------------------------ | ------------ |
| Research Agent       | Must-Have    | Generate requirements spec from a one-liner idea with clarification loop | Backend ✅   |
| Wireframe Agent      | Must-Have    | Generate architecture spec (site map, component tree, global state)      | Backend ✅   |
| Code Agent           | Must-Have    | Generate production files using full project context (Gemini 1.5 Pro)    | Backend ✅   |
| QA Agent             | Must-Have    | Code review with severity scoring (critical/warning/info)                | Backend ✅   |
| Builder Pipeline     | Must-Have    | Full Research → Wireframe → Code → QA pipeline with retry loop           | Backend ✅   |
| GitHub Export        | Must-Have    | Push generated code to a new GitHub repository                           | Backend ✅   |
| AI Refactoring       | Should-Have  | Select code and request AI-powered refactoring                           | Backend ✅   |
| IDE Simulation       | Should-Have  | Monaco Editor with file tree, code viewing, diff view                    | Frontend TBD |
| RAG Pattern Matching | Nice-to-Have | Enrich agents with previous successful architectural patterns            | Backend ✅   |

### 3.2 Student Mode Features

| Feature            | Priority    | Description                                                     | Status       |
| ------------------ | ----------- | --------------------------------------------------------------- | ------------ |
| Skill Assessment   | Must-Have   | Adaptive quiz to determine beginner/intermediate/advanced       | Frontend TBD |
| Roadmap Generation | Must-Have   | AI-generated learning curriculum with modules and prerequisites | Backend ✅   |
| Choice Framework   | Must-Have   | 3-option decision cards for architectural choices               | Backend ✅   |
| Socratic Mentoring | Must-Have   | AI mentor that gives hints, not answers                         | Backend ✅   |
| Session Tracking   | Should-Have | Transcript history with concepts covered and duration           | Backend ✅   |
| Progress Dashboard | Should-Have | Module completion tracking with percentage                      | Backend ✅   |
| Code Sandbox       | Should-Have | In-browser code execution (Sandpack)                            | Frontend TBD |

### 3.3 Infrastructure Features

| Feature               | Priority     | Description                              | Status |
| --------------------- | ------------ | ---------------------------------------- | ------ |
| JWT Authentication    | Must-Have    | Supabase Auth with GitHub OAuth          | ✅     |
| Rate Limiting         | Must-Have    | Token bucket (60 req/min per IP/user)    | ✅     |
| CSRF Protection       | Must-Have    | Double-submit cookie with Bearer bypass  | ✅     |
| Input Validation      | Must-Have    | Pydantic v2 strict mode on all endpoints | ✅     |
| Error Sanitization    | Must-Have    | No internal details exposed to clients   | ✅     |
| Persistent Task Queue | Must-Have    | Celery + Redis with crash recovery       | ✅     |
| Real-Time Updates     | Must-Have    | SSE streaming + Supabase Realtime        | ✅     |
| LLM Resilience        | Must-Have    | Circuit breaker + exponential backoff    | ✅     |
| Structured Logging    | Should-Have  | JSON logs with request tracing           | ✅     |
| Monitoring            | Nice-to-Have | Flower dashboard for Celery workers      | ✅     |

## 4. Non-Functional Requirements

### Performance

- Agent response time: < 60s for single agent, < 5min for full pipeline
- API response time: < 100ms for non-agent endpoints
- SSE event latency: < 1s from status change to client notification

### Scalability

- Celery workers horizontally scalable (add workers to increase throughput)
- Stateless FastAPI instances behind load balancer
- Redis for shared state between workers

### Security

- RLS on all database tables (user isolation)
- No unvalidated user input reaches agents or database
- All secrets from environment variables, validated at startup
- HTTPS enforced in production

### Reliability

- Circuit breaker prevents cascade failures on LLM outages
- `task_acks_late` ensures no task loss on worker crashes
- Graceful degradation (Celery → BackgroundTasks fallback)

## 5. Technical Constraints

- **LLM Cost:** GPT-4o for reasoning, Gemini 1.5 Pro for code (1M context), Claude 3.5 Sonnet for pedagogy — model router optimizes cost vs. capability
- **Token Limits:** Research/Wireframe specs must fit within Gemini context for Code Agent consumption
- **Concurrency:** Long-running agents (30s-5min) require background execution — cannot block HTTP request threads
- **Supabase Limits:** Free tier has connection limits; service role key used only by backend

## 6. Success Metrics

| Metric                    | Target                             | Measurement                    |
| ------------------------- | ---------------------------------- | ------------------------------ |
| Idea → GitHub Repo time   | < 10 minutes                       | Track pipeline completion time |
| Agent success rate        | > 90%                              | Jobs completed without failure |
| QA pass rate              | > 80% on first attempt             | Fewer code→QA retries          |
| Student concept retention | > 70% quiz accuracy                | Post-module assessment         |
| User activation           | 60% of signups create a project    | Supabase analytics             |
| Builder conversion        | 40% of projects exported to GitHub | Track export events            |

## 7. User Journeys

Detailed user journeys are documented in [App_Flow.md](App_Flow.md).

## 8. Technical Architecture

Full technical stack and architecture details in [Tech_Stack.md](Tech_Stack.md).

## 9. Database Schema

Complete schema, RLS policies, and API contracts in [Backend_Schema.md](Backend_Schema.md).
