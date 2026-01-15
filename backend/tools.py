"""GitHub and Gemini tools for the GitHub Issue Solver."""

import os
import re
from typing import Dict, List, Optional
from dotenv import load_dotenv
from github import Github, GithubException
import google.generativeai as genai

# Load environment variables
load_dotenv()

# GitHub configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO_OWNER = os.getenv("GITHUB_REPO_OWNER")
GITHUB_REPO_NAME = os.getenv("GITHUB_REPO_NAME")

# Gemini configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)


def get_github_client() -> Github:
    """Get authenticated GitHub client."""
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN not found in environment variables")
    return Github(GITHUB_TOKEN)


def get_repository():
    """Get the repository object."""
    if not GITHUB_REPO_OWNER or not GITHUB_REPO_NAME:
        raise ValueError("GITHUB_REPO_OWNER and GITHUB_REPO_NAME must be set")
    client = get_github_client()
    return client.get_repo(f"{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}")


def extract_issue_number_from_url(url: str) -> Optional[int]:
    """Extract issue number from GitHub issue URL."""
    pattern = r"github\.com/[^/]+/[^/]+/issues/(\d+)"
    match = re.search(pattern, url)
    if match:
        return int(match.group(1))
    return None


def fetch_issue(issue_url: str) -> Dict:
    """Fetch issue details from GitHub.
    
    Args:
        issue_url: URL of the GitHub issue
        
    Returns:
        Dictionary containing issue details
    """
    try:
        issue_number = extract_issue_number_from_url(issue_url)
        if not issue_number:
            raise ValueError(f"Could not extract issue number from URL: {issue_url}")
        
        repo = get_repository()
        issue = repo.get_issue(issue_number)
        
        # Fetch comments
        comments = [comment.body for comment in issue.get_comments()]
        
        return {
            "number": issue.number,
            "title": issue.title,
            "body": issue.body or "",
            "status": issue.state,
            "labels": [label.name for label in issue.labels],
            "comments": comments,
            "url": issue.html_url,
        }
    except GithubException as e:
        raise Exception(f"GitHub API error: {e}")


def post_comment(issue_url: str, comment: str) -> bool:
    """Post a comment to a GitHub issue.
    
    Args:
        issue_url: URL of the GitHub issue
        comment: Comment text to post
        
    Returns:
        True if successful, False otherwise
    """
    try:
        issue_number = extract_issue_number_from_url(issue_url)
        if not issue_number:
            raise ValueError(f"Could not extract issue number from URL: {issue_url}")
        
        repo = get_repository()
        issue = repo.get_issue(issue_number)
        issue.create_comment(comment)
        return True
    except GithubException as e:
        raise Exception(f"Failed to post comment: {e}")


def close_issue(issue_url: str) -> bool:
    """Close a GitHub issue.
    
    Args:
        issue_url: URL of the GitHub issue
        
    Returns:
        True if successful, False otherwise
    """
    try:
        issue_number = extract_issue_number_from_url(issue_url)
        if not issue_number:
            raise ValueError(f"Could not extract issue number from URL: {issue_url}")
        
        repo = get_repository()
        issue = repo.get_issue(issue_number)
        issue.edit(state="closed")
        return True
    except GithubException as e:
        raise Exception(f"Failed to close issue: {e}")


def get_gemini_model(model_name: str = "gemini-pro"):
    """Get the Gemini model instance."""
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    return genai.GenerativeModel(model_name)


def generate_with_gemini(prompt: str, model_name: str = "gemini-pro") -> str:
    """Generate response using Gemini model.
    
    Args:
        prompt: The prompt to send to the model
        model_name: Name of the model to use
        
    Returns:
        Generated text response
    """
    try:
        model = get_gemini_model(model_name)
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        raise Exception(f"Gemini API error: {e}")


def analyze_issue_with_gemini(issue_title: str, issue_body: str, labels: List[str], comments: List[str]) -> Dict:
    """Analyze a GitHub issue using Gemini.
    
    Args:
        issue_title: Title of the issue
        issue_body: Body content of the issue
        labels: List of labels on the issue
        comments: List of comments on the issue
        
    Returns:
        Dictionary containing analysis results
    """
    from prompts import ISSUE_ANALYSIS_PROMPT
    
    prompt = ISSUE_ANALYSIS_PROMPT.format(
        title=issue_title,
        body=issue_body,
        labels=", ".join(labels) if labels else "None",
        comments="\n".join(comments) if comments else "No comments"
    )
    
    response = generate_with_gemini(prompt)
    
    # Parse the response to extract structured data
    return {
        "analysis": response,
        "issue_type": _extract_issue_type(response),
        "complexity": _extract_complexity(response),
    }


def generate_solution_with_gemini(issue_title: str, analysis: str, issue_type: str, complexity: str) -> str:
    """Generate a solution for the issue using Gemini.
    
    Args:
        issue_title: Title of the issue
        analysis: Analysis of the issue
        issue_type: Type of the issue
        complexity: Complexity level
        
    Returns:
        Generated solution text
    """
    from prompts import SOLUTION_GENERATION_PROMPT
    
    prompt = SOLUTION_GENERATION_PROMPT.format(
        title=issue_title,
        analysis=analysis,
        issue_type=issue_type,
        complexity=complexity
    )
    
    return generate_with_gemini(prompt)


def generate_code_changes_with_gemini(issue_title: str, issue_body: str, solution: str) -> str:
    """Generate code changes using Gemini.
    
    Args:
        issue_title: Title of the issue
        issue_body: Body content of the issue
        solution: Proposed solution
        
    Returns:
        Generated code changes
    """
    from prompts import CODE_CHANGE_PROMPT
    
    prompt = CODE_CHANGE_PROMPT.format(
        title=issue_title,
        body=issue_body,
        solution=solution
    )
    
    return generate_with_gemini(prompt)


def create_final_response(issue_title: str, solution: str, code_changes: str) -> str:
    """Create a final response to post to the issue.
    
    Args:
        issue_title: Title of the issue
        solution: Proposed solution
        code_changes: Code changes to implement
        
    Returns:
        Final response text
    """
    from prompts import FINAL_RESPONSE_PROMPT
    
    prompt = FINAL_RESPONSE_PROMPT.format(
        title=issue_title,
        solution=solution,
        code_changes=code_changes
    )
    
    return generate_with_gemini(prompt)


def _extract_issue_type(analysis: str) -> str:
    """Extract issue type from analysis text."""
    analysis_lower = analysis.lower()
    if "bug" in analysis_lower:
        return "bug"
    elif "feature" in analysis_lower:
        return "feature"
    elif "question" in analysis_lower or "help" in analysis_lower:
        return "question"
    elif "documentation" in analysis_lower:
        return "documentation"
    return "other"


def _extract_complexity(analysis: str) -> str:
    """Extract complexity level from analysis text."""
    analysis_lower = analysis.lower()
    if "high" in analysis_lower:
        return "high"
    elif "medium" in analysis_lower:
        return "medium"
    return "low"