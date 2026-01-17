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

export interface FileConfidence {
  file: string;
  confidence: number;
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
  file_confidences?: FileConfidence[];
  error?: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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