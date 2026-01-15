"""FastAPI entrypoint for GitHub Issue Solver."""

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional

from state import GraphState
from graph import app

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Create FastAPI app
fastapi_app = FastAPI(
    title="GitHub Issue Solver",
    description="AI-powered GitHub issue solver using LangGraph and Gemini",
    version="0.1.0",
)


class AnalyzeRequest(BaseModel):
    """Request model for analyzing an issue."""
    issue_url: str


class AnalyzeResponse(BaseModel):
    """Response model for analyzing an issue."""
    success: bool
    issue: Optional[dict] = None
    files: Optional[list] = None
    code: Optional[dict] = None
    reasoning: Optional[str] = None
    patch: Optional[str] = None
    error: Optional[str] = None


@fastapi_app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    """Analyze a GitHub issue.
    
    Args:
        request: Request containing the issue URL
        
    Returns:
        Response with the analysis and patch
    """
    # Initialize state
    initial_state = GraphState(
        issue_url=request.issue_url,
        issue={},
        files=[],
        code={},
        reasoning="",
        patch=""
    )
    
    try:
        # Run the graph
        result = app.invoke(initial_state)
        
        # Return JSON
        return AnalyzeResponse(
            success=True,
            issue=result.get("issue"),
            files=result.get("files"),
            code=result.get("code"),
            reasoning=result.get("reasoning"),
            patch=result.get("patch"),
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(fastapi_app, host=host, port=port)