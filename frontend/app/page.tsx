"use client";

import { useState, useEffect, useRef } from "react";
import ReactMarkdown, { Components } from "react-markdown";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { analyzeIssue, analyzeIssueStream, fetchRelatedIssues, AnalyzeResponse, StreamEvent, MentionedIssue } from "@/lib/api";

const markdownComponents: Components = {
  h1: ({ children }) => (
    <h1 className="text-2xl font-bold text-blue-600 dark:text-blue-400">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-xl font-semibold text-blue-500 dark:text-blue-300">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-lg font-medium text-blue-400 dark:text-blue-200">{children}</h3>
  ),
  h4: ({ children }) => (
    <h4 className="text-base font-medium text-blue-300 dark:text-blue-100">{children}</h4>
  ),
  p: ({ children }) => <p className="mb-2 last:mb-0 text-lg">{children}</p>,
  ul: ({ children }) => <ul className="mb-2 list-disc pl-5 last:mb-0 text-lg">{children}</ul>,
  ol: ({ children }) => <ol className="mb-2 list-decimal pl-5 last:mb-0 text-lg">{children}</ol>,
  li: ({ children }) => <li className="mb-1 text-lg">{children}</li>,
  code: ({ children, className }) => {
    const isInline = !className;
    if (isInline) {
      return <code className="rounded bg-gray-100 px-1 py-0.5 text-base dark:bg-gray-800 dark:text-gray-100">{children}</code>;
    }
    return <code className="text-base dark:text-gray-100">{children}</code>;
  },
  pre: ({ children }) => (
    <pre className="overflow-x-auto rounded bg-gray-100 p-2 text-base dark:bg-gray-800 dark:text-gray-100">{children}</pre>
  ),
};

// Helper function to check if a string has meaningful content
const hasContent = (value: string | undefined | null): boolean => {
  return value !== undefined && value !== null && value.trim().length > 0;
};

// Typewriter hook for streaming text
function useTypewriter(text: string, speed: number = 10) {
  const [displayedText, setDisplayedText] = useState("");
  const indexRef = useRef(0);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Reset when text changes
    indexRef.current = 0;
    setDisplayedText("");
    
    if (text.length === 0) return;

    // Clear any existing timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    const type = () => {
      if (indexRef.current < text.length) {
        setDisplayedText(text.slice(0, indexRef.current + 1));
        indexRef.current += 1;
        timeoutRef.current = setTimeout(type, speed);
      }
    };

    type();

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [text, speed]);

  return displayedText;
}

export default function Page() {
  const [issueUrl, setIssueUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<string>("");
  const [streamingReasoning, setStreamingReasoning] = useState<string>("");
  const [streamingPatch, setStreamingPatch] = useState<string>("");
  const [relatedIssues, setRelatedIssues] = useState<MentionedIssue[]>([]);
  const [loadingRelatedIssues, setLoadingRelatedIssues] = useState(false);

  // Typewriter effect for streaming text
  const displayedReasoning = useTypewriter(streamingReasoning, 10);
  const displayedPatch = useTypewriter(streamingPatch, 10);

  const handleFetchRelatedIssues = async () => {
    if (!result?.candidate_files || result.candidate_files.length === 0) return;
    
    setLoadingRelatedIssues(true);
    try {
      const issues = await fetchRelatedIssues(issueUrl, result.candidate_files);
      setRelatedIssues(issues);
    } catch (err) {
      console.error("Failed to fetch related issues:", err);
    } finally {
      setLoadingRelatedIssues(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);
    setStreamingReasoning("");
    setStreamingPatch("");
    setStatus("");

    try {
      // Use streaming API
      for await (const event of analyzeIssueStream(issueUrl)) {
        if (event.type === "status") {
          setStatus(event.data as string);
        } else if (event.type === "reasoning") {
          setStreamingReasoning((prev) => prev + (event.data as string));
        } else if (event.type === "patch") {
          setStreamingPatch((prev) => prev + (event.data as string));
        } else if (event.type === "complete") {
          const data = event.data as {
            success: boolean;
            issue?: AnalyzeResponse["issue"];
            files?: string[];
            code?: Record<string, unknown>;
            reasoning?: string;
            patch?: string;
            repo_context?: AnalyzeResponse["repo_context"];
            candidate_directories?: string[];
            candidate_files?: string[];
            file_reasons?: AnalyzeResponse["file_reasons"];
            investigation_plan?: AnalyzeResponse["investigation_plan"];
            mentioned_issues?: AnalyzeResponse["mentioned_issues"];
          };
          setResult({
            success: data.success,
            issue: data.issue,
            files: data.files,
            code: data.code,
            reasoning: data.reasoning,
            patch: data.patch,
            repo_context: data.repo_context,
            candidate_directories: data.candidate_directories,
            candidate_files: data.candidate_files,
            file_reasons: data.file_reasons,
            investigation_plan: data.investigation_plan,
            mentioned_issues: data.mentioned_issues,
          });
          setStatus("");
        } else if (event.type === "error") {
          setError(event.data as string);
          setStatus("");
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-svh p-6">
        <div className="flex max-w-4xl min-w-0 flex-col gap-6 text-lg leading-loose mx-auto">
       <div className="flex flex-col gap-4">
  <h1 className="text-7xl font-extrabold">
    Github Issue Solver
  </h1>
  <p className="text-lg text-muted-foreground">
    Enter a GitHub issue URL to get AI-powered analysis and code fixes.
  </p>
</div>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <Input
            type="url"
            placeholder="https://github.com/owner/repo/issues/123"
            value={issueUrl}
            onChange={(e) => setIssueUrl(e.target.value)}
            className="flex-1"
            required
          />
          <Button type="submit" disabled={loading}>
            {loading ? "Analyzing..." : "Analyze"}
          </Button>
        </form>

        {error && (
          <Card className="border-red-500">
            <CardHeader>
              <CardTitle className="text-red-500">Error</CardTitle>
            </CardHeader>
            <CardContent>
              <p>{error}</p>
            </CardContent>
          </Card>
        )}

        {status && (
          <Card>
            <CardContent>
              <p className="text-base text-muted-foreground">{status}</p>
            </CardContent>
          </Card>
        )}

        {result && result.success && (
          <div className="space-y-4">
            {result.issue && (
              <Card>
                <CardHeader>
                  <CardTitle>Issue Details</CardTitle>
                  <CardDescription>
                    <a
                      href={result.issue.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-500 hover:underline"
                    >
                      #{result.issue.number}: {result.issue.title}
                    </a>
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {hasContent(result.issue.body) ? (
                    <ReactMarkdown components={markdownComponents}>{result.issue.body}</ReactMarkdown>
                  ) : (
                    <p className="text-muted-foreground">No description provided.</p>
                  )}
                  {result.issue.labels.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {result.issue.labels.map((label) => (
                        <span
                          key={label}
                          className="rounded bg-gray-100 px-2 py-1 text-base"
                        >
                          {label}
                        </span>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {result.file_reasons && result.file_reasons.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Ranked Files</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {result.file_reasons.map((fr) => (
                      <div key={fr.file} className="space-y-1">
                        <span className="font-mono text-base font-medium">{fr.file}</span>
                        <p className="text-base text-muted-foreground">{fr.reason}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {result.candidate_files && result.candidate_files.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Related Issues</CardTitle>
                </CardHeader>
                <CardContent>
                  <Button
                    onClick={handleFetchRelatedIssues}
                    disabled={loadingRelatedIssues}
                    variant="outline"
                    size="sm"
                  >
                    {loadingRelatedIssues ? "Loading..." : "Find Related Issues"}
                  </Button>
                  
                  {relatedIssues.length > 0 && (
                    <div className="mt-3 space-y-3">
                      {relatedIssues.map((issue) => (
                        <div key={issue.number} className="space-y-1">
                          <a
                            href={issue.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="font-mono text-base font-medium text-blue-500 hover:underline"
                          >
                            #{issue.number}: {issue.title}
                          </a>
                          {issue.mentioned_files && issue.mentioned_files.length > 0 && (
                            <div className="flex flex-wrap gap-1">
                              {issue.mentioned_files.map((file) => (
                                <span
                                  key={file}
                                  className="rounded bg-gray-100 px-1.5 py-0.5 text-base font-mono dark:bg-gray-800"
                                >
                                  {file}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                  
                  {!loadingRelatedIssues && relatedIssues.length === 0 && (
                    <p className="mt-2 text-base text-muted-foreground">
                      Click the button above to find issues mentioning these files.
                    </p>
                  )}
                </CardContent>
              </Card>
            )}

            {hasContent(displayedReasoning) && (
              <Card>
                <CardHeader>
                  <CardTitle>AI Reasoning</CardTitle>
                </CardHeader>
                <CardContent>
                  <ReactMarkdown components={markdownComponents}>{displayedReasoning}</ReactMarkdown>
                </CardContent>
              </Card>
            )}

            {hasContent(displayedPatch) && (
              <Card>
                <CardHeader>
                  <CardTitle>Generated Patch</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto rounded bg-gray-100 p-4 text-base dark:bg-gray-800 dark:text-gray-100">
                    <ReactMarkdown components={markdownComponents}>{displayedPatch}</ReactMarkdown>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}