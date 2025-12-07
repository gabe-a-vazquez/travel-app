# Travel App

A travel itinerary planning app with an LLM-powered chat interface. Built with FastAPI (Python) backend and Next.js frontend.

## Project Structure

```
travel-app/
├── apps/
│   ├── api/          # FastAPI backend (Python)
│   └── web/          # Next.js frontend (TypeScript)
├── packages/
│   └── shared/       # Shared types (future use)
├── package.json      # Root workspace config
└── pnpm-workspace.yaml
```

## Prerequisites

- Node.js 18+
- pnpm 8+
- Python 3.11+
- A Google AI Studio API key (for Gemini and ADK)

## Setup

### 1. Install frontend dependencies

```bash
pnpm install
```

### 2. Install backend dependencies

```bash
cd apps/api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

**Backend (`apps/api/.env`):**
```
GEMINI_API_KEY=your_gemini_api_key_here
GOOGLE_API_KEY=your_google_api_key_here
```

> Note: You can use the same API key from Google AI Studio for both `GEMINI_API_KEY` and `GOOGLE_API_KEY`.

**Frontend (`apps/web/.env.local`):**
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running Locally

### Option 1: Run both services together

```bash
pnpm dev
```

### Option 2: Run services separately

**Backend (terminal 1):**
```bash
pnpm dev:api
```

**Frontend (terminal 2):**
```bash
pnpm dev:web
```

### Option 3: Run Google ADK Web UI

To use the Google Agent Development Kit (ADK) web interface with Gemini:

```bash
pnpm dev:adk
```

This will start the ADK web UI on port 8001. The ADK provides an interactive interface to chat with the travel assistant agent powered by Gemini 2.5 Flash with Google Search capabilities.

> **Note**: The ADK web UI is for development and debugging only, not for production use.

### Access the app

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs
- ADK Web UI: http://localhost:8001 (when running `pnpm dev:adk`)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/chat` | Send a message to the LLM |

### Example request

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'
```

## Deployment (Railway)

Both services are configured for Railway deployment:

1. Create a new project on Railway
2. Add two services from this repo:
   - `apps/api` → Set root directory to `apps/api`
   - `apps/web` → Set root directory to `apps/web`
3. Set environment variables:
   - **api**: `GEMINI_API_KEY`
   - **web**: `NEXT_PUBLIC_API_URL` (use the API service's public URL)

## Tech Stack

- **Backend**: FastAPI, Uvicorn, Google Generative AI (Gemini), Google ADK
- **Frontend**: Next.js 14, React, TypeScript, Tailwind CSS, shadcn/ui
- **Deployment**: Railway

## Google ADK Integration

This project includes Google's Agent Development Kit (ADK), which provides:

- **Travel Assistant Agent**: A specialized agent configured for travel planning
- **Google Search Integration**: The agent can search for current travel information
- **Interactive Web UI**: Development interface for testing and debugging
- **Model**: Gemini 2.5 Flash for fast, efficient responses

### ADK Features

The travel assistant agent (`apps/api/src/services/adk_agent.py`) is configured to:
- Help users plan trips and itineraries
- Provide information about destinations and attractions
- Answer travel-related questions
- Use Google Search for up-to-date information

### Running the ADK

Use the command `pnpm dev:adk` to start the ADK web interface. The agent will be available at http://localhost:8001 where you can interact with it through a chat interface.
