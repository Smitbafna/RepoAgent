"""LangGraph workflow for GitHub Issue Solver."""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from state import GraphState
from tools import fetch_issue, extract_repo_info_from_url, call_gemini
from prompts import PLANNER_PROMPT, REASONING_PROMPT, PATCH_PROMPT


def fetch_issue_node(state: GraphState) -> Dict[str, Any]:
    """Node to fetch issue details from GitHub."""
    issue = fetch_issue(state["issue_url"])
    owner, repo_name = extract_repo_info_from_url(state["issue_url"])
    return {"issue": issue, "owner": owner, "repo_name": repo_name}


def planner_node(state: GraphState) -> Dict[str, Any]:
    """Node to plan the solution using Gemini."""
    prompt = PLANNER_PROMPT.format(
        title=state["issue"]["title"],
        body=state["issue"]["body"]
    )
    reasoning = call_gemini(prompt)
    return {"reasoning": reasoning}


def find_files_node(state: GraphState) -> Dict[str, Any]:
    """Node to find relevant files in the repository."""
    # For now, return empty files list - can be enhanced later
    return {"files": []}


def reason_node(state: GraphState) -> Dict[str, Any]:
    """Node to reason through the solution."""
    prompt = REASONING_PROMPT.format(
        title=state["issue"]["title"],
        body=state["issue"]["body"],
        repo_info=f"{state.get('owner', '')}/{state.get('repo_name', '')}",
        files=state.get("files", [])
    )
    reasoning = call_gemini(prompt)
    return {"reasoning": reasoning}


def generate_fix_node(state: GraphState) -> Dict[str, Any]:
    """Node to generate the fix patch."""
    prompt = PATCH_PROMPT.format(
        title=state["issue"]["title"],
        body=state["issue"]["body"],
        reasoning=state["reasoning"],
        files=state.get("files", [])
    )
    patch = call_gemini(prompt)
    return {"patch": patch}


def create_graph() -> StateGraph:
    """Create and configure the LangGraph workflow."""
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("fetch_issue", fetch_issue_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("find_files", find_files_node)
    workflow.add_node("reason", reason_node)
    workflow.add_node("generate_fix", generate_fix_node)
    
    # Add edges
    workflow.add_edge("fetch_issue", "planner")
    workflow.add_edge("planner", "find_files")
    workflow.add_edge("find_files", "reason")
    workflow.add_edge("reason", "generate_fix")
    workflow.add_edge("generate_fix", END)
    
    # Set entry point
    workflow.set_entry_point("fetch_issue")
    
    return workflow


# Create the graph instance
graph = create_graph()
app = graph.compile()