"""State definitions for the GitHub Issue Solver graph."""

from typing import TypedDict, List, Optional


class GraphState(TypedDict):
    """State for the GitHub Issue Solver workflow."""
    issue_url: str
    issue: dict
    files: list
    code: dict
    reasoning: str
    patch: str
    owner: str
    repo_name: str
    repo_context: dict
    candidate_directories: list
    candidate_files: list
    file_confidences: list  # List of {file: str, confidence: float} objects