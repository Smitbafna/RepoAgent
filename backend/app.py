"""FastAPI entrypoint for GitHub Issue Solver."""

import os
import json
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional

from state import GraphState
from graph import app, stream_analysis
from tools import extract_repo_info_from_url

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Create FastAPI app
fastapi_app = FastAPI(
    title="GitHub Issue Solver",
    description="AI-powered GitHub issue solver using LangGraph and Gemini",
    version="0.1.0",
)

# Add CORS middleware
fastapi_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (configure for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    repo_context: Optional[dict] = None
    candidate_directories: Optional[list] = None
    candidate_files: Optional[list] = None
    file_reasons: Optional[list] = None
    investigation_plan: Optional[dict] = None
    mentioned_issues: Optional[list] = None
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
        patch="",
        owner="",
        repo_name="",
        repo_context={},
        candidate_directories=[],
        candidate_files=[],
        file_reasons=[],
        investigation_plan={},
        mentioned_issues=[]
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
            repo_context=result.get("repo_context"),
            candidate_directories=result.get("candidate_directories"),
            candidate_files=result.get("candidate_files"),
            file_reasons=result.get("file_reasons"),
            investigation_plan=result.get("investigation_plan"),
            mentioned_issues=result.get("mentioned_issues") or [],
        )
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


async def event_generator(issue_url: str):
    """Generate SSE events for streaming analysis."""
    async for event in stream_analysis(issue_url):
        yield f"data: {json.dumps(event)}\n\n"


class RelatedIssuesRequest(BaseModel):
    """Request model for fetching related issues."""
    issue_url: str
    candidate_files: list


class RelatedIssuesResponse(BaseModel):
    """Response model for related issues."""
    success: bool
    mentioned_issues: list
    error: Optional[str] = None


@fastapi_app.post("/related-issues", response_model=RelatedIssuesResponse)
async def get_related_issues(request: RelatedIssuesRequest):
    """Fetch related issues for candidate files.
    
    This endpoint is called on-demand from the frontend to find issues
    that mention the candidate files.
    
    Args:
        request: Request containing the issue URL and candidate files
        
    Returns:
        Response with related issues
    """
    from tools import search_issues_by_mentioned_files
    
    try:
        # Extract owner and repo from the issue URL
        repo_info = extract_repo_info_from_url(request.issue_url)
        if not repo_info:
            raise HTTPException(status_code=400, detail="Invalid issue URL")
        
        owner, repo_name = repo_info
        
        # Search for issues mentioning the candidate files
        mentioned_issues = search_issues_by_mentioned_files(
            owner, repo_name, request.candidate_files
        )
        
        return RelatedIssuesResponse(
            success=True,
            mentioned_issues=mentioned_issues
        )
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@fastapi_app.post("/analyze/stream")
async def analyze_stream(request: AnalyzeRequest):
    """Stream the analysis of a GitHub issue.
    
    Args:
        request: Request containing the issue URL
        
    Returns:
        Server-Sent Events stream with analysis progress
    """
    return StreamingResponse(
        event_generator(request.issue_url),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(fastapi_app, host=host, port=port)