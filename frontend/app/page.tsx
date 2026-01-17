"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { analyzeIssue, AnalyzeResponse } from "@/lib/api";

export default function Page() {
  const [issueUrl, setIssueUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await analyzeIssue(issueUrl);
      setResult(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-svh p-6">
      <div className="flex max-w-4xl min-w-0 flex-col gap-6 text-sm leading-loose">
        <div>
          <h1 className="font-medium text-2xl">GitHub Issue Solver</h1>
          <p className="text-muted-foreground">
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
                  <p className="whitespace-pre-wrap">{result.issue.body}</p>
                  {result.issue.labels.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {result.issue.labels.map((label) => (
                        <span
                          key={label}
                          className="rounded bg-gray-100 px-2 py-1 text-xs"
                        >
                          {label}
                        </span>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {result.file_confidences && result.file_confidences.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Ranked Files</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {result.file_confidences.map((fc) => (
                      <div key={fc.file} className="flex items-center justify-between">
                        <span className="font-mono text-xs">{fc.file}</span>
                        <span className="rounded bg-blue-100 px-2 py-1 text-xs font-medium">
                          {(fc.confidence * 100).toFixed(0)}% confidence
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {result.reasoning && (
              <Card>
                <CardHeader>
                  <CardTitle>AI Reasoning</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="whitespace-pre-wrap">{result.reasoning}</p>
                </CardContent>
              </Card>
            )}

            {result.patch && (
              <Card>
                <CardHeader>
                  <CardTitle>Generated Patch</CardTitle>
                </CardHeader>
                <CardContent>
                  <pre className="overflow-x-auto rounded bg-gray-100 p-4 text-xs">
                    <code>{result.patch}</code>
                  </pre>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
}