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


def extract_repo_info_from_url(url: str) -> Optional[tuple]:
    """Extract owner and repo name from GitHub issue URL."""
    pattern = r"github\.com/([^/]+)/([^/]+)/issues/\d+"
    match = re.search(pattern, url)
    if match:
        return match.group(1), match.group(2)
    return None


def extract_issue_number_from_url(url: str) -> Optional[int]:
    """Extract issue number from GitHub issue URL."""
    pattern = r"github\.com/[^/]+/[^/]+/issues/(\d+)"
    match = re.search(pattern, url)
    if match:
        return int(match.group(1))
    return None


def fetch_issue(issue_url: str) -> dict:
    """Fetch issue details from GitHub.
    
    Args:
        issue_url: URL of the GitHub issue
        
    Returns:
        Dictionary containing issue details
    """
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN not found in environment variables")
    
    issue_number = extract_issue_number_from_url(issue_url)
    if not issue_number:
        raise ValueError(f"Could not extract issue number from URL: {issue_url}")
    
    repo_info = extract_repo_info_from_url(issue_url)
    if not repo_info:
        raise ValueError(f"Could not extract repo info from URL: {issue_url}")
    
    owner, repo_name = repo_info
    client = Github(GITHUB_TOKEN)
    repo = client.get_repo(f"{owner}/{repo_name}")
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


def fetch_repo() -> dict:
    """Fetch repository information.
    
    Returns:
        Dictionary containing repository details
    """
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN not found in environment variables")
    
    if not GITHUB_REPO_OWNER or not GITHUB_REPO_NAME:
        raise ValueError("GITHUB_REPO_OWNER and GITHUB_REPO_NAME must be set")
    
    client = Github(GITHUB_TOKEN)
    repo = client.get_repo(f"{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}")
    
    return {
        "name": repo.name,
        "full_name": repo.full_name,
        "description": repo.description,
        "language": repo.language,
        "default_branch": repo.default_branch,
    }


def read_file(file_path: str, owner: str = None, repo_name: str = None) -> str:
    """Read a file from the repository.
    
    Args:
        file_path: Path to the file in the repository
        owner: Repository owner (extracted from env if not provided)
        repo_name: Repository name (extracted from env if not provided)
        
    Returns:
        File contents as string
    """
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN not found in environment variables")
    
    if not owner or not repo_name:
        if not GITHUB_REPO_OWNER or not GITHUB_REPO_NAME:
            raise ValueError("GITHUB_REPO_OWNER and GITHUB_REPO_NAME must be set")
        owner = GITHUB_REPO_OWNER
        repo_name = GITHUB_REPO_NAME
    
    client = Github(GITHUB_TOKEN)
    repo = client.get_repo(f"{owner}/{repo_name}")
    
    try:
        file_content = repo.get_contents(file_path)
        return file_content.decoded_content.decode("utf-8")
    except GithubException as e:
        raise Exception(f"Failed to read file: {e}")


def search_issues(query: str) -> List[dict]:
    """Search for issues in the repository.
    
    Args:
        query: Search query string
        
    Returns:
        List of matching issues
    """
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN not found in environment variables")
    
    if not GITHUB_REPO_OWNER or not GITHUB_REPO_NAME:
        raise ValueError("GITHUB_REPO_OWNER and GITHUB_REPO_NAME must be set")
    
    client = Github(GITHUB_TOKEN)
    repo = client.get_repo(f"{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}")
    
    issues = repo.get_issues(state="open")
    results = []
    
    for issue in issues:
        if query.lower() in issue.title.lower() or query.lower() in (issue.body or "").lower():
            results.append({
                "number": issue.number,
                "title": issue.title,
                "url": issue.html_url,
            })
    
    return results


def call_gemini(prompt: str, model_name: str = "gemini-flash-lite-latest") -> str:
    """Call Gemini API with a prompt.
    
    Args:
        prompt: The prompt to send to the model
        model_name: Name of the model to use
        
    Returns:
        Generated text response
    """
    if not GOOGLE_API_KEY:
        raise ValueError("GOOGLE_API_KEY not found in environment variables")
    
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    return response.text
