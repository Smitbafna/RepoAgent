# RepoAgent

AI-powered GitHub issue solver that automatically analyzes issues, identifies relevant files, and generates code fixes using LangGraph and Gemini.

## Features

- **Issue Analysis**: Enter any GitHub issue URL to get AI-powered analysis
- **Smart File Discovery**: Automatically identifies relevant source files in the repository
- **Code Generation**: Generates patches and fixes based on issue requirements
- **Streaming Responses**: Real-time streaming of AI reasoning and patch generation
- **Related Issues**: Find other issues that mention the same files

## Architecture

- **Frontend**: Next.js with shadcn/ui components
- **Backend**: FastAPI with LangGraph workflow
- **AI**: Google Gemini for code analysis and generation
- **GitHub API**: PyGithub for repository and issue data

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