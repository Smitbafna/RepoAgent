"""All prompts for the GitHub Issue Solver."""

PLANNER_PROMPT = """
You are an expert software engineer analyzing a GitHub issue.

Issue Title: {title}
Issue Body: {body}

Analyze this issue and provide:
1. A clear understanding of the problem
2. The type of issue (bug, feature, question, documentation)
3. Key files that likely need to be modified
4. A plan for solving this issue

Keep your response concise and focused.
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