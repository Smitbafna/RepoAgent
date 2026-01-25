"""LangGraph workflow for GitHub Issue Solver."""

import json
import asyncio
from typing import Dict, Any, AsyncGenerator
from langgraph.graph import StateGraph, END
from state import GraphState
from tools import fetch_issue, extract_repo_info_from_url, build_repo_context, format_repo_context_for_prompt, call_gemini, call_gemini_streaming
from prompts import PLANNER_PROMPT, REASONING_PROMPT, PATCH_PROMPT, RANK_FILES_PROMPT


def extract_json_from_response(response: str) -> Any:
    """Extract JSON from a response that may contain extra text.
    
    Args:
        response: Raw response from Gemini
        
    Returns:
        Parsed JSON object or None if parsing fails
    """
    # Try to find JSON in the response
    response = response.strip()
    
    # Check if response looks like it starts with a newline (common issue)
    if response.startswith('\n') or response.startswith('\r'):
        response = response.lstrip('\r\n')
    
    # Try direct parsing first
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        pass
    
    # Try to find JSON array or object in the response
    # Use a more robust approach to find balanced brackets
    def find_balanced_json(text: str, start_char: str, end_char: str) -> str:
        """Find balanced JSON by counting brackets."""
        if start_char not in text:
            return None
        start_idx = text.find(start_char)
        if start_idx == -1:
            return None
        
        count = 0
        in_string = False
        escape = False
        
        for i in range(start_idx, len(text)):
            char = text[i]
            if escape:
                escape = False
                continue
            if char == '\\' and in_string:
                escape = True
                continue
            if char == '"':
                in_string = not in_string
            elif not in_string:
                if char == start_char:
                    count += 1
                elif char == end_char:
                    count -= 1
                    if count == 0:
                        return text[start_idx:i+1]
        return None
    
    # Try to find JSON array
    array_json = find_balanced_json(response, '[', ']')
    if array_json:
        try:
            parsed = json.loads(array_json)
            # Ensure it's a valid list
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
    
    # Try to find JSON object
    object_json = find_balanced_json(response, '{', '}')
    if object_json:
        try:
            parsed = json.loads(object_json)
            # Ensure it's a valid dict
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
    
    return None


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
    try:
        repo_context = state.get("repo_context", {})
        formatted_context = format_repo_context_for_prompt(repo_context)
        issue = state.get("issue", {})
        prompt = PLANNER_PROMPT.format(
            title=issue.get("title", ""),
            body=issue.get("body", ""),
            labels=issue.get("labels", []),
            repo_context=formatted_context
        )
        response = call_gemini(prompt)
        result = extract_json_from_response(response)
        if result is None or not isinstance(result, dict):
            # Log the response for debugging
            print(f"DEBUG: planner_node response: {response[:200]}...")
            return {"reasoning": response, "candidate_directories": []}
        return {
            "reasoning": result.get("reasoning", response),
            "candidate_directories": result.get("directories", [])
        }
    except Exception as e:
        print(f"DEBUG: planner_node error: {e}")
        return {"reasoning": f"Error in planner: {e}", "candidate_directories": []}


def find_files_node(state: GraphState) -> Dict[str, Any]:
    """Node to find relevant files in the repository."""
    # Use candidate_directories from planner output to filter files
    candidate_directories = state.get("candidate_directories", [])
    repo_context = state.get("repo_context", {})
    
    # Ensure candidate_directories is a list
    if not isinstance(candidate_directories, list):
        candidate_directories = []
    
    all_files = repo_context.get("tree", [])
    
    if candidate_directories:
        # Filter files to only include those in the identified directories
        files = [f for f in all_files if any(f.startswith(d) for d in candidate_directories)]
    else:
        # Use all source files from the tree when no directories are specified
        files = all_files
    
    return {"files": files}


def rank_files_node(state: GraphState) -> Dict[str, Any]:
    """Node to rank files for inspection using Gemini."""
    files = state.get("files", [])
    issue = state.get("issue", {})
    prompt = RANK_FILES_PROMPT.format(
        title=issue.get("title", ""),
        body=issue.get("body", ""),
        labels=issue.get("labels", []),
        files=files
    )
    response = call_gemini(prompt)
    result = extract_json_from_response(response)
    if result is None or not isinstance(result, list):
        return {"candidate_files": files[:10], "file_reasons": []}
    # Extract file names and reasons from the response
    candidate_files = []
    file_reasons = []
    for item in result[:10]:  # Limit to 10 files
        if isinstance(item, dict) and "file" in item:
            candidate_files.append(item["file"])
            file_reasons.append({
                "file": item["file"],
                "reason": item.get("reason", "")
            })
    return {
        "candidate_files": candidate_files,
        "file_reasons": file_reasons
    }


def save_investigation_plan_node(state: GraphState) -> Dict[str, Any]:
    """Node to save the investigation plan with directories, files, and reasons."""
    candidate_directories = state.get("candidate_directories", [])
    candidate_files = state.get("candidate_files", [])
    file_reasons = state.get("file_reasons", [])
    
    investigation_plan = {
        "directories": candidate_directories,
        "files": candidate_files,
        "reasons": file_reasons
    }
    
    return {"investigation_plan": investigation_plan}


def reason_node(state: GraphState) -> Dict[str, Any]:
    """Node to reason through the solution."""
    repo_context = state.get("repo_context", {})
    formatted_context = format_repo_context_for_prompt(repo_context)
    issue = state.get("issue", {})
    prompt = REASONING_PROMPT.format(
        title=issue.get("title", ""),
        body=issue.get("body", ""),
        repo_info=f"{state.get('owner', '')}/{state.get('repo_name', '')}",
        files=state.get("files", []),
        repo_context=formatted_context
    )
    reasoning = call_gemini(prompt)
    return {"reasoning": reasoning}


def generate_fix_node(state: GraphState) -> Dict[str, Any]:
    """Node to generate the fix patch."""
    issue = state.get("issue", {})
    prompt = PATCH_PROMPT.format(
        title=issue.get("title", ""),
        body=issue.get("body", ""),
        reasoning=state.get("reasoning", ""),
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
    workflow.add_node("save_investigation_plan", save_investigation_plan_node)
    workflow.add_node("reason", reason_node)
    workflow.add_node("generate_fix", generate_fix_node)
    
    # Add edges
    workflow.add_edge("fetch_issue", "fetch_repo_context")
    workflow.add_edge("fetch_repo_context", "planner")
    workflow.add_edge("planner", "find_files")
    workflow.add_edge("find_files", "rank_files")
    workflow.add_edge("rank_files", "save_investigation_plan")
    workflow.add_edge("save_investigation_plan", "reason")
    workflow.add_edge("reason", "generate_fix")
    workflow.add_edge("generate_fix", END)
    
    # Set entry point
    workflow.set_entry_point("fetch_issue")
    
    return workflow


# Create the graph instance
graph = create_graph()
app = graph.compile()


# Streaming version
async def stream_analysis(issue_url: str) -> AsyncGenerator[Dict[str, Any], None]:
    """Stream the analysis process with events.
    
    Uses concurrent streaming - each step starts as soon as the previous one completes,
    and results are streamed token-by-token.
    
    Args:
        issue_url: URL of the GitHub issue
        
    Yields:
        Events with type and data
    """
    # Initialize state
    state = {
        "issue_url": issue_url,
        "issue": {},
        "files": [],
        "code": {},
        "reasoning": "",
        "patch": "",
        "owner": "",
        "repo_name": "",
        "repo_context": {},
        "candidate_directories": [],
        "candidate_files": [],
        "file_reasons": [],
        "investigation_plan": {},
        "mentioned_issues": []
    }
    
    try:
        # Step 1: Fetch issue
        yield {"type": "status", "data": "Fetching issue details..."}
        state.update(fetch_issue_node(state))
        # Stream the fetched issue details
        issue = state.get("issue", {})
        if issue:
            yield {"type": "issue", "data": issue}
        
        # Step 2: Fetch repo context
        yield {"type": "status", "data": "Fetching repository context..."}
        state.update(fetch_repo_context_node(state))
        
        # Step 3: Planner
        yield {"type": "status", "data": "Planning solution..."}
        state.update(planner_node(state))
        
        # Step 4: Find files
        yield {"type": "status", "data": "Finding relevant files..."}
        state.update(find_files_node(state))
        
        # Step 5: Rank files
        yield {"type": "status", "data": "Ranking files by relevance..."}
        state.update(rank_files_node(state))
        
        # Step 6: Save investigation plan
        state.update(save_investigation_plan_node(state))
        
        # Step 7: Reason (stream this)
        yield {"type": "status", "data": "Generating reasoning..."}
        repo_context = state.get("repo_context", {})
        formatted_context = format_repo_context_for_prompt(repo_context)
        issue = state.get("issue", {})
        prompt = REASONING_PROMPT.format(
            title=issue.get("title", ""),
            body=issue.get("body", ""),
            repo_info=f"{state.get('owner', '')}/{state.get('repo_name', '')}",
            files=state.get("files", []),
            repo_context=formatted_context
        )
        
        # Stream reasoning
        reasoning_text = ""
        async for chunk in call_gemini_streaming(prompt):
            reasoning_text += chunk
            yield {"type": "reasoning", "data": chunk}
        state["reasoning"] = reasoning_text
        
        # Step 8: Generate fix (stream this)
        yield {"type": "status", "data": "Generating patch..."}
        patch_prompt = PATCH_PROMPT.format(
            title=issue.get("title", ""),
            body=issue.get("body", ""),
            reasoning=state.get("reasoning", ""),
            files=state.get("files", [])
        )
        
        # Stream patch
        patch_text = ""
        async for chunk in call_gemini_streaming(patch_prompt):
            patch_text += chunk
            yield {"type": "patch", "data": chunk}
        state["patch"] = patch_text
        
        # Final result
        yield {"type": "complete", "data": {
            "success": True,
            "issue": state.get("issue"),
            "files": state.get("files"),
            "code": state.get("code"),
            "reasoning": state.get("reasoning"),
            "patch": state.get("patch"),
            "repo_context": state.get("repo_context"),
            "candidate_directories": state.get("candidate_directories"),
            "candidate_files": state.get("candidate_files"),
            "file_reasons": state.get("file_reasons"),
            "investigation_plan": state.get("investigation_plan"),
            "mentioned_issues": [],
        }}
        
    except Exception as e:
        import traceback
        error_detail = f"{str(e)}\n{traceback.format_exc()}"
        yield {"type": "error", "data": error_detail}
