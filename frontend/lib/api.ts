/** API client for GitHub Issue Solver backend */

export interface AnalyzeRequest {
  issue_url: string;
}

export interface RepoContext {
  language?: string;
  default_branch?: string;
  source_dirs?: string[];
  test_dirs?: string[];
  workflow_dirs?: string[];
  important_files?: string[];
  tree?: string[];
}

export interface FileReason {
  file: string;
  reason: string;
}

export interface MentionedIssue {
  number: number;
  title: string;
  url: string;
  mentioned_files: string[];
}

export interface AnalyzeResponse {
  success: boolean;
  issue?: {
    number: number;
    title: string;
    body: string;
    status: string;
    labels: string[];
    comments: string[];
    url: string;
  };
  files?: string[];
  code?: Record<string, unknown>;
  reasoning?: string;
  patch?: string;
  repo_context?: RepoContext;
  candidate_directories?: string[];
  candidate_files?: string[];
  file_reasons?: FileReason[];
  investigation_plan?: {
    directories: string[];
    files: string[];
    reasons: FileReason[];
  };
  mentioned_issues?: MentionedIssue[];
  error?: string;
}

// Streaming event types
export interface StreamEvent {
  type: "status" | "reasoning" | "patch" | "complete" | "error";
  data: string | {
    success: boolean;
    issue?: AnalyzeResponse["issue"];
    files?: string[];
    code?: Record<string, unknown>;
    reasoning?: string;
    patch?: string;
    repo_context?: RepoContext;
    candidate_directories?: string[];
    candidate_files?: string[];
    file_reasons?: FileReason[];
    investigation_plan?: AnalyzeResponse["investigation_plan"];
    mentioned_issues?: MentionedIssue[];
  };
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function fetchRelatedIssues(
  issueUrl: string,
  candidateFiles: string[]
): Promise<MentionedIssue[]> {
  const response = await fetch(`${API_BASE_URL}/related-issues`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ issue_url: issueUrl, candidate_files: candidateFiles }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to fetch related issues");
  }

  const data = await response.json();
  return data.mentioned_issues || [];
}

export async function analyzeIssue(issueUrl: string): Promise<AnalyzeResponse> {
  const response = await fetch(`${API_BASE_URL}/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ issue_url: issueUrl }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to analyze issue");
  }

  return response.json();
}

export async function* analyzeIssueStream(
  issueUrl: string
): AsyncGenerator<StreamEvent, void> {
  const response = await fetch(`${API_BASE_URL}/analyze/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ issue_url: issueUrl }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to analyze issue");
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    throw new Error("No response body");
  }

  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();

    if (done) {
      break;
    }

    buffer += decoder.decode(value, { stream: true });

    // Process complete SSE events (separated by double newlines)
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";

    for (const event of events) {
      if (event.startsWith("data: ")) {
        const jsonStr = event.slice(6);
        try {
          const parsed: StreamEvent = JSON.parse(jsonStr);
          yield parsed;
        } catch (e) {
          console.error("Failed to parse SSE event:", e);
        }
      }
    }
  }
}