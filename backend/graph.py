"""LangGraph workflow for GitHub Issue Solver."""

import json
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from state import GraphState
from tools import fetch_issue, extract_repo_info_from_url, build_repo_context, format_repo_context_for_prompt, call_gemini
from prompts import PLANNER_PROMPT, REASONING_PROMPT, PATCH_PROMPT, RANK_FILES_PROMPT


def fetch_issue_node(state: GraphState) -> Dict[str, Any]:
    """Node to fetch issue details from GitHub."""
    issue = fetch_issue(state["issue_url"])
    owner, repo_name = extract_repo_info_from_url(state["issue_url"])
    return {"issue": issue, "owner": owner, "repo_name": repo_name}


def fetch_repo_context_node(state: GraphState) -> Dict[str, Any]:
    """Node to fetch repository context."""
    repo_context = build_repo_context(state["owner"], state["repo_name"])
    return {"repo_context": repo_context}


def planner_node(state: GraphState) -> Dict[str, Any]:
    """Node to plan the solution using Gemini."""
    repo_context = state.get("repo_context", {})
    formatted_context = format_repo_context_for_prompt(repo_context)
    prompt = PLANNER_PROMPT.format(
        title=state["issue"]["title"],
        body=state["issue"]["body"],
        labels=state["issue"].get("labels", []),
        repo_context=formatted_context
    )
    response = call_gemini(prompt)
    try:
        result = json.loads(response)
        return {
            "reasoning": result.get("reasoning", response),
            "candidate_directories": result.get("directories", [])
        }
    except json.JSONDecodeError:
        return {"reasoning": response, "candidate_directories": []}


def find_files_node(state: GraphState) -> Dict[str, Any]:
    """Node to find relevant files in the repository."""
    # Use candidate_directories from planner output to filter files
    candidate_directories = state.get("candidate_directories", [])
    repo_context = state.get("repo_context", {})
    
    if candidate_directories:
        # Filter files to only include those in the identified directories
        all_files = repo_context.get("tree", [])
        files = [f for f in all_files if any(f.startswith(d) for d in candidate_directories)]
    else:
        files = repo_context.get("source_dirs", [])
    
    return {"files": files}


def rank_files_node(state: GraphState) -> Dict[str, Any]:
    """Node to rank files for inspection using Gemini."""
    files = state.get("files", [])
    prompt = RANK_FILES_PROMPT.format(
        title=state["issue"]["title"],
        body=state["issue"]["body"],
        labels=state["issue"].get("labels", []),
        files=files
    )
    response = call_gemini(prompt)
    try:
        result = json.loads(response)
        return {"candidate_files": result.get("files", [])[:10]}  # Limit to 10 files
    except json.JSONDecodeError:
        return {"candidate_files": files[:10]}


def reason_node(state: GraphState) -> Dict[str, Any]:
    """Node to reason through the solution."""
    repo_context = state.get("repo_context", {})
    formatted_context = format_repo_context_for_prompt(repo_context)
    prompt = REASONING_PROMPT.format(
        title=state["issue"]["title"],
        body=state["issue"]["body"],
        repo_info=f"{state.get('owner', '')}/{state.get('repo_name', '')}",
        files=state.get("files", []),
        repo_context=formatted_context
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
    workflow.add_node("fetch_repo_context", fetch_repo_context_node)
    workflow.add_node("planner", planner_node)
    workflow.add_node("find_files", find_files_node)
    workflow.add_node("rank_files", rank_files_node)
    workflow.add_node("reason", reason_node)
    workflow.add_node("generate_fix", generate_fix_node)
    
    # Add edges
    workflow.add_edge("fetch_issue", "fetch_repo_context")
    workflow.add_edge("fetch_repo_context", "planner")
    workflow.add_edge("planner", "find_files")
    workflow.add_edge("find_files", "rank_files")
    workflow.add_edge("rank_files", "reason")
    workflow.add_edge("reason", "generate_fix")
    workflow.add_edge("generate_fix", END)
    
    # Set entry point
    workflow.set_entry_point("fetch_issue")
    
    return workflow


# Create the graph instance
graph = create_graph()
app = graph.compile()
