"""All prompts for the GitHub Issue Solver."""

PLANNER_PROMPT = """
You are a senior software engineer.

Given:

1. GitHub Issue
2. Repository Structure

Determine which parts of the repository are most likely involved.

Return ONLY JSON. Do not include any other text, explanations, or markdown formatting.

Output:

{{
  "directories": [],
  "reasoning": ""
}}

Issue Title: {title}
Issue Description: {body}
Labels: {labels}
Repository Context: {repo_context}
"""

REASONING_PROMPT = """
You are an expert software engineer. Based on the issue and repository context, reason through the solution.

Issue: {title}
Issue Body: {body}
Repository: {repo_info}
Files Found: {files}

Repository Context:
{repo_context}

Think through:
1. What is the root cause of the issue?
2. What changes are needed?
3. What is the best approach to implement the fix?

Provide your reasoning step by step.
"""

PATCH_PROMPT = """
You are an expert software engineer. Generate the exact code changes needed to fix this issue.

Issue: {title}
Issue Body: {body}
Reasoning: {reasoning}
Files to Modify: {files}

Provide the code changes in a clear format showing:
1. File path
2. The exact changes needed (diff format or code blocks)
3. Any new files to create

Be precise and include complete code snippets.
"""

RANK_FILES_PROMPT = """
You are a senior software engineer.

Here are the files available in the repository.

Which ones should be inspected first?

Return at most 10 files.

Return ONLY a valid JSON array. Do not include any other text, explanations, or markdown formatting.

Output:

[
  {{
    "file": "pkg/webhooks/server.go",
    "reason": "The issue is related to workflow failures involving controller startup, and this file initializes webhook services."
  }},
  {{
    "file": "pkg/webhooks/register.go",
    "reason": "This file handles webhook registration and may contain the logic causing the startup failure."
  }}
]

Issue Title: {title}
Issue Description: {body}
Labels: {labels}
Available Files: {files}
"""

REVIEW_PROMPT = """
Review the proposed changes for this GitHub issue.

Issue: {title}
Issue Body: {body}
Patch: {patch}

Evaluate:
1. Does the patch correctly address the issue?
2. Are there any edge cases or potential issues?
3. Is the code quality good?

Provide feedback and approval status.
"""
