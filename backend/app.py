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
    version="0.1.0"
)


class SolveIssueRequest(BaseModel):
    """Request model for solving an issue."""
    issue_url: str
    dry_run: Optional[bool] = False


class SolveIssueResponse(BaseModel):
    """Response model for solving an issue."""
    success: bool
    issue_number: Optional[int] = None
    issue_title: Optional[str] = None
    analysis: Optional[str] = None
    solution: Optional[str] = None
    code_changes: Optional[str] = None
    final_response: Optional[str] = None
    error: Optional[str] = None


@fastapi_app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "GitHub Issue Solver API", "status": "running"}


@fastapi_app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@fastapi_app.post("/solve", response_model=SolveIssueResponse)
async def solve_issue(request: SolveIssueRequest):
    """Solve a GitHub issue.
    
    Args:
        request: Request containing the issue URL
        
    Returns:
        Response with the solution and analysis
    """
    # Initialize state
    initial_state = GraphState(
        issue_url=request.issue_url
    )
    
    try:
        # Run the graph
        result = app.invoke(initial_state)
        
        # Convert result to response
        response = SolveIssueResponse(
            success=True,
            issue_number=result.get("issue_number"),
            issue_title=result.get("issue_title"),
            analysis=result.get("issue_analysis"),
            solution=result.get("proposed_solution"),
            code_changes=result.get("code_changes"),
            final_response=result.get("final_response"),
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@fastapi_app.post("/analyze", response_model=SolveIssueResponse)
async def analyze_issue(request: SolveIssueRequest):
    """Analyze a GitHub issue without posting a response.
    
    Args:
        request: Request containing the issue URL
        
    Returns:
        Response with the analysis and solution
    """
    # Initialize state
    initial_state = GraphState(
        issue_url=request.issue_url
    )
    
    try:
        # Run the graph but stop before posting
        result = app.invoke(initial_state)
        
        # Convert result to response
        response = SolveIssueResponse(
            success=True,
            issue_number=result.get("issue_number"),
            issue_title=result.get("issue_title"),
            analysis=result.get("issue_analysis"),
            solution=result.get("proposed_solution"),
            code_changes=result.get("code_changes"),
            final_response=result.get("final_response"),
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    
    uvicorn.run(fastapi_app, host=host, port=port)