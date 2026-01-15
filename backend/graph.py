"""LangGraph workflow for GitHub Issue Solver."""

from typing import Dict, Any
from langgraph.graph import StateGraph, END
from state import GraphState
from tools import (
    fetch_issue,
    analyze_issue_with_gemini,
    generate_solution_with_gemini,
    generate_code_changes_with_gemini,
    create_final_response,
    post_comment,
)


def fetch_issue_node(state: GraphState) -> Dict[str, Any]:
    """Node to fetch issue details from GitHub."""
    if not state.issue_url:
        return {"error": "No issue URL provided"}
    
    try:
        issue_data = fetch_issue(state.issue_url)
        return {
            "issue_number": issue_data["number"],
            "issue_title": issue_data["title"],
            "issue_body": issue_data["body"],
            "issue_status": issue_data["status"],
            "issue_labels": issue_data["labels"],
            "issue_comments": issue_data["comments"],
        }
    except Exception as e:
        return {"error": str(e)}


def analyze_issue_node(state: GraphState) -> Dict[str, Any]:
    """Node to analyze the issue using Gemini."""
    if not state.issue_title or not state.issue_body:
        return {"error": "Issue not fetched yet"}
    
    try:
        analysis = analyze_issue_with_gemini(
            state.issue_title,
            state.issue_body,
            state.issue_labels,
            state.issue_comments
        )
        return {
            "issue_analysis": analysis["analysis"],
            "issue_type": analysis["issue_type"],
            "complexity": analysis["complexity"],
        }
    except Exception as e:
        return {"error": str(e)}


def generate_solution_node(state: GraphState) -> Dict[str, Any]:
    """Node to generate solution for the issue."""
    if not state.issue_analysis:
        return {"error": "Issue not analyzed yet"}
    
    try:
        solution = generate_solution_with_gemini(
            state.issue_title,
            state.issue_analysis,
            state.issue_type,
            state.complexity
        )
        return {"proposed_solution": solution}
    except Exception as e:
        return {"error": str(e)}


def generate_code_node(state: GraphState) -> Dict[str, Any]:
    """Node to generate code changes."""
    if not state.proposed_solution:
        return {"error": "Solution not generated yet"}
    
    try:
        code_changes = generate_code_changes_with_gemini(
            state.issue_title,
            state.issue_body,
            state.proposed_solution
        )
        return {"code_changes": code_changes}
    except Exception as e:
        return {"error": str(e)}


def create_response_node(state: GraphState) -> Dict[str, Any]:
    """Node to create final response."""
    if not state.code_changes:
        return {"error": "Code changes not generated yet"}
    
    try:
        response = create_final_response(
            state.issue_title,
            state.proposed_solution,
            state.code_changes
        )
        return {"final_response": response}
    except Exception as e:
        return {"error": str(e)}


def post_response_node(state: GraphState) -> Dict[str, Any]:
    """Node to post response to GitHub issue."""
    if not state.final_response or not state.issue_url:
        return {"error": "Response not created or no issue URL"}
    
    try:
        post_comment(state.issue_url, state.final_response)
        return {"next_step": "completed"}
    except Exception as e:
        return {"error": str(e)}


def should_continue(state: GraphState) -> str:
    """Determine the next step in the workflow."""
    if state.error:
        return "error"
    
    if not state.issue_title:
        return "fetch_issue"
    
    if not state.issue_analysis:
        return "analyze_issue"
    
    if not state.proposed_solution:
        return "generate_solution"
    
    if not state.code_changes:
        return "generate_code"
    
    if not state.final_response:
        return "create_response"
    
    if not state.next_step:
        return "post_response"
    
    return "completed"


def create_graph() -> StateGraph:
    """Create and configure the LangGraph workflow."""
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("fetch_issue", fetch_issue_node)
    workflow.add_node("analyze_issue", analyze_issue_node)
    workflow.add_node("generate_solution", generate_solution_node)
    workflow.add_node("generate_code", generate_code_node)
    workflow.add_node("create_response", create_response_node)
    workflow.add_node("post_response", post_response_node)
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "fetch_issue",
        should_continue,
        {
            "fetch_issue": "fetch_issue",
            "analyze_issue": "analyze_issue",
            "error": END,
        }
    )
    
    workflow.add_conditional_edges(
        "analyze_issue",
        should_continue,
        {
            "analyze_issue": "analyze_issue",
            "generate_solution": "generate_solution",
            "error": END,
        }
    )
    
    workflow.add_conditional_edges(
        "generate_solution",
        should_continue,
        {
            "generate_solution": "generate_solution",
            "generate_code": "generate_code",
            "error": END,
        }
    )
    
    workflow.add_conditional_edges(
        "generate_code",
        should_continue,
        {
            "generate_code": "generate_code",
            "create_response": "create_response",
            "error": END,
        }
    )
    
    workflow.add_conditional_edges(
        "create_response",
        should_continue,
        {
            "create_response": "create_response",
            "post_response": "post_response",
            "error": END,
        }
    )
    
    workflow.add_conditional_edges(
        "post_response",
        should_continue,
        {
            "post_response": "post_response",
            "completed": END,
            "error": END,
        }
    )
    
    # Set entry point
    workflow.set_entry_point("fetch_issue")
    
    return workflow


# Create the graph instance
graph = create_graph()
app = graph.compile()