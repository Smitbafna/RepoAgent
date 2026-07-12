# RepoAgent

AI-powered GitHub issue solver that takes a GitHub issue URL and automatically analyzes the problem, identifies relevant files in the repository, and generates code fixes. The application uses a LangGraph workflow with Gemini AI to fetch issue details, explore repository context, plan solutions, and stream real-time reasoning and patch generation to a Next.js frontend.

## Features

- **Issue Analysis**: Fetches and parses GitHub issue details including title, body, labels, and comments
- **Repository Context**: Explores repository structure, language, and file tree using GitHub API
- **Smart File Discovery**: Uses AI to identify relevant source directories and rank candidate files
- **AI Reasoning**: Generates step-by-step analysis of the issue and solution approach
- **Code Generation**: Creates patches and code fixes based on issue requirements
- **Streaming Responses**: Real-time Server-Sent Events (SSE) streaming of AI reasoning and patch generation
- **Related Issues**: Finds other open issues that mention the same candidate files
- **Typewriter Effect**: Frontend displays streaming text with smooth typewriter animation

## Architecture

- **Frontend**: Next.js with shadcn/ui components, TypeScript, and React Markdown
- **Backend**: FastAPI with LangGraph StateGraph workflow for orchestration
- **AI**: Google Gemini (gemini-3.1-flash-lite) for code analysis and generation
- **GitHub API**: PyGithub for repository and issue data fetching
- **Workflow**: 8-node LangGraph pipeline (fetch_issue → fetch_repo_context → planner → find_files → rank_files → save_investigation_plan → reason → generate_fix)

## Setup

### Prerequisites

- Python 3.10+
- Node.js 18+
- GitHub Personal Access Token
- Google API Key (for Gemini)

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file in the backend directory:

```
GITHUB_TOKEN=your_github_token
GOOGLE_API_KEY=your_google_api_key
```

Run the backend:

```bash
python3 app.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Usage

1. Start both backend and frontend servers
2. Open the frontend in your browser
3. Enter a GitHub issue URL (e.g., `https://github.com/owner/repo/issues/123`)
4. Click "Analyze" to get AI-powered analysis and code fixes

## API Endpoints

- `POST /analyze` - Analyze a GitHub issue (non-streaming)
- `POST /analyze/stream` - Stream analysis with real-time updates
- `POST /related-issues` - Find issues mentioning specific files

## Environment Variables

- `GITHUB_TOKEN` - GitHub API token
- `GOOGLE_API_KEY` - Google Gemini API key
- `HOST` - Backend host (default: 0.0.0.0)
- `PORT` - Backend port (default: 8000)
