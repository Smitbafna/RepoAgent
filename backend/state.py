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