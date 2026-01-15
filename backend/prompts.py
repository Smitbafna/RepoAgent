"""All prompts for the GitHub Issue Solver."""

# Prompt for analyzing GitHub issues
ISSUE_ANALYSIS_PROMPT = """
You are an expert software engineer analyzing a GitHub issue. 

Please analyze the following GitHub issue and provide:
1. A clear understanding of the problem
2. The type of issue (bug, feature request, question, documentation, etc.)
3. The complexity level (low, medium, high)
4. Key technical details

Issue Title: {title}
Issue Body: {body}
Labels: {labels}
Comments: {comments}

Please provide a structured analysis.
"""

# Prompt for generating solutions
SOLUTION_GENERATION_PROMPT = """
You are an expert software engineer tasked with solving a GitHub issue.

Based on the issue analysis below, generate a detailed solution:

Issue: {title}
Analysis: {analysis}
Issue Type: {issue_type}
Complexity: {complexity}

Please provide:
1. A clear explanation of the solution approach
2. Specific code changes needed (with file paths and code snippets)
3. Any potential edge cases or considerations
"""

# Prompt for generating code changes
CODE_CHANGE_PROMPT = """
You are an expert software engineer. Generate the exact code changes needed to fix this issue.

Issue: {title}
Issue Body: {body}
Proposed Solution: {solution}

Please provide:
1. The file(s) that need to be modified
2. The exact code changes (in diff format or code blocks)
3. Any new files that need to be created
"""

# Prompt for creating final response
FINAL_RESPONSE_PROMPT = """
You are a helpful GitHub assistant. Create a professional response to the issue author.

Issue: {title}
Solution: {solution}
Code Changes: {code_changes}

Please write a clear, helpful response that:
1. Acknowledges the issue
2. Explains the solution
3. Provides the code changes
4. Offers to help with any questions
"""

# Prompt for determining next action
NEXT_ACTION_PROMPT = """
Based on the current state, determine the next action:

Current State:
- Issue URL: {issue_url}
- Issue fetched: {issue_fetched}
- Analysis done: {analysis_done}
- Solution generated: {solution_generated}
- Code changes ready: {code_changes_ready}

What should be the next step? (fetch_issue, analyze_issue, generate_solution, generate_code, create_response, post_response, error)
"""