# Travel App Setup Plan

## Overview
Set up a monorepo with a Python (FastAPI) backend and Next.js frontend, using Google Gemini as the LLM, hosted on Railway.

## Project Structure
```
/travel-app
├── apps/
│   ├── web/                 # Next.js frontend
│   │   ├── src/
│   │   │   ├── app/         # App router pages
│   │   │   ├── components/  # React components
│   │   │   └── lib/         # Utilities
│   │   ├── package.json
│   │   └── next.config.js
│   └── api/                 # FastAPI backend
│       ├── src/
│       │   ├── main.py      # FastAPI app entry
│       │   ├── routers/     # API routes
│       │   └── services/    # Business logic (LLM calls)
│       ├── requirements.txt
│       └── pyproject.toml
├── packages/
│   └── shared/              # Shared TypeScript types (for future use)
├── package.json             # Root package.json (workspaces)
├── pnpm-workspace.yaml      # pnpm workspace config
└── README.md
```

---

## Step 1: Initialize Monorepo Structure ✅ DONE

### Tasks:
1. ✅ Create root directory and initialize git
2. ✅ Create folder structure (`apps/web`, `apps/api`, `packages/shared`)
3. ✅ Set up pnpm workspaces with root `package.json` and `pnpm-workspace.yaml`

---

## Step 2: Set Up Python Backend (FastAPI) ✅ DONE

### Tasks:
1. ✅ Create `apps/api/pyproject.toml` with dependencies:
   - fastapi
   - uvicorn
   - google-generativeai (Gemini SDK)
   - python-dotenv
   - pydantic
2. ✅ Create `apps/api/requirements.txt` (for Railway compatibility)
3. ✅ Create `apps/api/src/main.py` with:
   - FastAPI app instance
   - CORS middleware (allow frontend origin)
   - Health check endpoint (`GET /health`)
4. ✅ Create `apps/api/src/routers/chat.py` with:
   - `POST /api/chat` endpoint accepting `{ "message": "string" }`
5. ✅ Create `apps/api/src/services/llm.py` with:
   - Gemini client initialization
   - Function to send prompt and get response
6. ✅ Create `apps/api/.env.example` with required env vars

---

## Step 3: Set Up Next.js Frontend ✅ DONE

### Tasks:
1. ✅ Initialize Next.js app in `apps/web` with:
   - TypeScript
   - App Router
   - Tailwind CSS
   - ESLint
2. ✅ Install and configure shadcn/ui:
   - Run `npx shadcn@latest init`
   - Add components: Button, Input, Card
3. ✅ Create main chat page (`apps/web/src/app/page.tsx`):
   - Text input for user prompt
   - Submit button
   - Response display area
4. ✅ Create API client (`apps/web/src/lib/api.ts`):
   - Function to call backend `/api/chat`
5. ✅ Create `apps/web/.env.example` with `NEXT_PUBLIC_API_URL`

---

## Step 4: Configure Railway Deployment ✅ DONE

### Tasks:
1. ✅ Create `apps/api/railway.json` (or use Railway dashboard):
   - Build command: `pip install -r requirements.txt`
   - Start command: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
2. ✅ Create `apps/web/railway.json`:
   - Build command: `pnpm install && pnpm build`
   - Start command: `pnpm start`
3. ✅ Document environment variables needed:
   - API: `GEMINI_API_KEY`
   - Web: `NEXT_PUBLIC_API_URL` (Railway internal URL or public URL)

---

## Step 5: Local Development Setup ✅ DONE

### Tasks:
1. ✅ Create root `README.md` with:
   - Project overview
   - Setup instructions
   - How to run locally
2. ✅ Create convenience scripts in root `package.json`:
   - `dev:web` - run Next.js dev server
   - `dev:api` - run FastAPI with uvicorn
   - `dev` - run both concurrently

---

## Step 6: Test End-to-End ✅ DONE

### Tasks:
1. ✅ Start backend locally (`uvicorn`)
2. ✅ Start frontend locally (`pnpm dev`)
3. ⏳ Submit a test prompt via UI (ready for manual testing)
4. ⏳ Verify response from Gemini appears in UI (ready for manual testing)

---

## Environment Variables Required

| Service | Variable | Description |
|---------|----------|-------------|
| API | `GEMINI_API_KEY` | Google AI Studio API key |
| Web | `NEXT_PUBLIC_API_URL` | Backend URL (e.g., `http://localhost:8000` locally) |

---

## Commands Reference

```bash
# Install dependencies
pnpm install                      # Frontend deps
cd apps/api && pip install -r requirements.txt  # Backend deps

# Run locally
pnpm dev:api                      # Start FastAPI on :8000
pnpm dev:web                      # Start Next.js on :3000

# Or run both
pnpm dev
```

---

## Next Steps After Basic Setup
- Add Amadeus API integration for travel search
- Add itinerary data models
- Expand UI with search forms and results display
- Add database for saving itineraries (Railway Postgres)
