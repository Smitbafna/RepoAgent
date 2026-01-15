"""State definitions for the GitHub Issue Solver graph."""

from typing import List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class IssueStatus(str, Enum):
    """Status of the GitHub issue."""
    OPEN = "open"
    CLOSED = "closed"
    IN_PROGRESS = "in_progress"


class GraphState(BaseModel):
    """State for the GitHub Issue Solver workflow."""
    
    # Input
    issue_url: Optional[str] = Field(default=None, description="URL of the GitHub issue to solve")
    issue_number: Optional[int] = Field(default=None, description="Issue number")
    
    # Issue data
    issue_title: Optional[str] = Field(default=None, description="Title of the GitHub issue")
    issue_body: Optional[str] = Field(default=None, description="Body content of the GitHub issue")
    issue_status: Optional[IssueStatus] = Field(default=None, description="Current status of the issue")
    issue_labels: List[str] = Field(default_factory=list, description="Labels on the GitHub issue")
    issue_comments: List[str] = Field(default_factory=list, description="Comments on the GitHub issue")
    
    # Analysis
    issue_analysis: Optional[str] = Field(default=None, description="AI analysis of the issue")
    issue_type: Optional[str] = Field(default=None, description="Type of issue (bug, feature, question, etc.)")
    complexity: Optional[str] = Field(default=None, description="Complexity level of the issue")
    
    # Solution
    proposed_solution: Optional[str] = Field(default=None, description="Proposed solution for the issue")
    code_changes: Optional[str] = Field(default=None, description="Code changes to fix the issue")
    
    # Output
    final_response: Optional[str] = Field(default=None, description="Final response to post")
    error: Optional[str] = Field(default=None, description="Error message if any")
    
    # Control flow
    next_step: Optional[str] = Field(default=None, description="Next step in the workflow")
    
    class Config:
        use_enum_values = True