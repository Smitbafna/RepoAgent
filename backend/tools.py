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

print("GITHUB_TOKEN:", repr(os.getenv("GITHUB_TOKEN")))
print("GITHUB_REPO_OWNER:", repr(os.getenv("GITHUB_REPO_OWNER")))
print("GITHUB_REPO_NAME:", repr(os.getenv("GITHUB_REPO_NAME")))

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


def fetch_repo_metadata(owner: str, repo_name: str) -> dict:
    """Fetch repository metadata for a given owner and repo.
    
    Args:
        owner: Repository owner
        repo_name: Repository name
        
    Returns:
        Dictionary containing repository metadata
    """
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN not found in environment variables")
    
    client = Github(GITHUB_TOKEN)
    repo = client.get_repo(f"{owner}/{repo_name}")
    
    return {
        "repo_name": repo.name,
        "description": repo.description,
        "default_branch": repo.default_branch,
        "language": repo.language,
        "stars": repo.stargazers_count,
    }


def fetch_repo_tree(owner: str, repo_name: str, branch: str = "main") -> list:
    """Fetch repository file tree (paths only, no contents).
    
    Args:
        owner: Repository owner
        repo_name: Repository name
        branch: Branch name (defaults to "main")
        
    Returns:
        List of file/directory paths in the repository
    """
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN not found in environment variables")
    
    client = Github(GITHUB_TOKEN)
    repo = client.get_repo(f"{owner}/{repo_name}")
    
    # Get the default branch if not specified
    if branch == "main" and repo.default_branch:
        branch = repo.default_branch
    
    # Get the tree recursively
    git_tree = repo.get_git_tree(branch, recursive=True)
    
    # Extract just the paths
    paths = [item.path for item in git_tree.tree]
    
    return paths


def clean_tree(paths: list) -> list:
    """Clean the repository tree by removing unnecessary paths.
    
    Removes:
    - vendor/
    - node_modules/
    - dist/
    - coverage/
    - generated/
    - bin/
    - Binary files (*.png, *.jpg, *.gif, *.pdf)
    
    Args:
        paths: List of file/directory paths
        
    Returns:
        Cleaned list of paths
    """
    # Directories to exclude
    exclude_dirs = {
        "vendor",
        "node_modules",
        "dist",
        "coverage",
        "generated",
        "bin",
    }
    
    # File extensions to exclude
    exclude_extensions = {".png", ".jpg", ".gif", ".pdf"}
    
    cleaned = []
    for path in paths:
        # Check if path starts with an excluded directory
        parts = path.split("/")
        if parts[0] in exclude_dirs:
            continue
        
        # Check if file has excluded extension
        if any(path.lower().endswith(ext) for ext in exclude_extensions):
            continue
        
        cleaned.append(path)
    
    return cleaned


def categorize_files(paths: list) -> dict:
    """Categorize files into source, tests, configs, docs, and github.
    
    Args:
        paths: List of file/directory paths
        
    Returns:
        Dictionary with categorized file lists
    """
    source_dirs = {"pkg", "cmd", "internal", "src", "lib", "app"}
    test_patterns = {"_test.go", "_test.py", "_test.js", "_test.ts", ".test.", "test/", "/test/", "_spec.", ".spec."}
    config_patterns = {"dockerfile", "makefile", "cmakelists", ".dockerignore", ".gitignore"}
    doc_patterns = {"readme", "docs", "documentation"}
    
    categories = {
        "source": [],
        "tests": [],
        "configs": [],
        "docs": [],
        "github": [],
    }
    
    for path in paths:
        path_lower = path.lower()
        parts = path.split("/")
        
        # Check for GitHub-related files
        if parts[0] == ".github":
            categories["github"].append(path)
            continue
        
        # Check for test files
        is_test = any(p in path_lower for p in test_patterns)
        if is_test:
            categories["tests"].append(path)
            continue
        
        # Check for config files (yaml/yml files)
        if path_lower.endswith(".yaml") or path_lower.endswith(".yml"):
            categories["configs"].append(path)
            continue
        
        # Check for other config files
        is_config = any(p in path_lower for p in config_patterns)
        if is_config:
            categories["configs"].append(path)
            continue
        
        # Check for docs
        is_doc = any(p in path_lower for p in doc_patterns)
        if is_doc:
            categories["docs"].append(path)
            continue
        
        # Check for source files (by directory)
        if parts[0] in source_dirs:
            categories["source"].append(path)
            continue
        
        # Check for source files (by extension)
        source_extensions = {".go", ".py", ".js", ".ts", ".java", ".cpp", ".c", ".rs", ".rb", ".php", ".swift", ".kt", ".scala", ".sh", ".pl", ".lua"}
        if any(path_lower.endswith(ext) for ext in source_extensions):
            categories["source"].append(path)
            continue
        
        # Skip files that don't fit any category (hidden files, etc.)
        # Don't add to source by default
    
    return categories


def build_repo_context(owner: str, repo_name: str) -> dict:
    """Build repository context for AI analysis.
    
    Args:
        owner: Repository owner
        repo_name: Repository name
        
    Returns:
        Dictionary containing repository context
    """
    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN not found in environment variables")
    
    # Fetch metadata
    metadata = fetch_repo_metadata(owner, repo_name)
    
    # Fetch and process tree
    tree = fetch_repo_tree(owner, repo_name)
    cleaned_tree = clean_tree(tree)
    categorized = categorize_files(cleaned_tree)
    
    # Extract unique directories
    source_dirs = sorted(set(
        path.split("/")[0] for path in categorized["source"] 
        if "/" in path
    ))
    test_dirs = sorted(set(
        path.split("/")[0] for path in categorized["tests"] 
        if "/" in path
    ))
    workflow_dirs = sorted(set(
        path.split("/")[0] for path in categorized["github"] 
        if "/" in path
    ))
    
    # Find important files (top-level only)
    important_files = []
    for path in cleaned_tree:
        if "/" not in path:  # Top-level file
            path_lower = path.lower()
            if any(path_lower.endswith(ext) for ext in [".go", ".py", ".js", ".ts", ".java", ".cpp", ".c", ".rs", ".rb", ".php", ".swift", ".kt", ".scala", ".sh", ".pl", ".lua"]):
                important_files.append(path)
            elif path_lower in ["go.mod", "package.json", "requirements.txt", "makefile", "dockerfile", "readme.md", "license", "changelog.md"]:
                important_files.append(path)
    
    return {
        "language": metadata.get("language"),
        "default_branch": metadata.get("default_branch"),
        "source_dirs": source_dirs,
        "test_dirs": test_dirs,
        "workflow_dirs": workflow_dirs,
        "important_files": important_files,
        "tree": cleaned_tree,
    }


def format_repo_context_for_prompt(repo_context: dict) -> str:
    """Format repository context for Gemini prompt.
    
    Creates a concise summary instead of dumping all paths.
    
    Args:
        repo_context: Repository context dictionary
        
    Returns:
        Formatted string for the prompt
    """
    lines = [
        "Repository Context:",
        f"Language: {repo_context.get('language', 'Unknown')}",
        f"Default branch: {repo_context.get('default_branch', 'main')}",
        "",
        "Top level directories:",
    ]
    
    # Add top-level directories
    all_dirs = set()
    for path in repo_context.get("tree", []):
        parts = path.split("/")
        if len(parts) > 1:
            all_dirs.add(parts[0])
    
    for d in sorted(all_dirs):
        lines.append(f"  {d}/")
    
    lines.append("")
    lines.append("Important files:")
    for f in repo_context.get("important_files", []):
        lines.append(f"  {f}")
    
    return "\n".join(lines)


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
