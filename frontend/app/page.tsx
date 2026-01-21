"use client";

import { useState } from "react";
import ReactMarkdown, { Components } from "react-markdown";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { analyzeIssue, AnalyzeResponse } from "@/lib/api";

const markdownComponents: Components = {
  h1: ({ children }) => (
    <h1 className="text-lg font-bold text-blue-600 dark:text-blue-400">{children}</h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-base font-semibold text-blue-500 dark:text-blue-300">{children}</h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-sm font-medium text-blue-400 dark:text-blue-200">{children}</h3>
  ),
  h4: ({ children }) => (
    <h4 className="text-xs font-medium text-blue-300 dark:text-blue-100">{children}</h4>
  ),
  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  ul: ({ children }) => <ul className="mb-2 list-disc pl-5 last:mb-0">{children}</ul>,
  ol: ({ children }) => <ol className="mb-2 list-decimal pl-5 last:mb-0">{children}</ol>,
  li: ({ children }) => <li className="mb-1">{children}</li>,
  code: ({ children, className }) => {
    const isInline = !className;
    if (isInline) {
      return <code className="rounded bg-gray-100 px-1 py-0.5 text-xs dark:bg-gray-800 dark:text-gray-100">{children}</code>;
    }
    return <code className="text-xs dark:text-gray-100">{children}</code>;
  },
  pre: ({ children }) => (
    <pre className="overflow-x-auto rounded bg-gray-100 p-2 text-xs dark:bg-gray-800 dark:text-gray-100">{children}</pre>
  ),
};

// Helper function to check if a string has meaningful content
const hasContent = (value: string | undefined | null): boolean => {
  return value !== undefined && value !== null && value.trim().length > 0;
};

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

            {result.file_reasons && result.file_reasons.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Ranked Files</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {result.file_reasons.map((fr) => (
                      <div key={fr.file} className="space-y-1">
                        <span className="font-mono text-xs font-medium">{fr.file}</span>
                        <p className="text-xs text-muted-foreground">{fr.reason}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

             {result.mentioned_issues && (
               <Card>
                 <CardHeader>
                   <CardTitle>Related Issues (Mentioned Files)</CardTitle>
                 </CardHeader>
                 <CardContent>
                   {result.mentioned_issues.length > 0 ? (
                     <div className="space-y-3">
                       {result.mentioned_issues.map((issue) => (
                         <div key={issue.number} className="space-y-1">
                           <a
                             href={issue.url}
                             target="_blank"
                             rel="noopener noreferrer"
                             className="font-mono text-xs font-medium text-blue-500 hover:underline"
                           >
                             #{issue.number}: {issue.title}
                           </a>
                           {issue.mentioned_files && issue.mentioned_files.length > 0 && (
                             <div className="flex flex-wrap gap-1">
                               {issue.mentioned_files.map((file) => (
                                 <span
                                   key={file}
                                   className="rounded bg-gray-100 px-1.5 py-0.5 text-xs font-mono dark:bg-gray-800"
                                 >
                                   {file}
                                 </span>
                               ))}
                             </div>
                           )}
                         </div>
                       ))}
                     </div>
                   ) : (
                     <p className="text-muted-foreground">No related issues found mentioning these files.</p>
                   )}
                 </CardContent>
               </Card>
             )}

            {hasContent(result.reasoning) && (
              <Card>
                <CardHeader>
                  <CardTitle>AI Reasoning</CardTitle>
                </CardHeader>
                <CardContent>
                  <ReactMarkdown components={markdownComponents}>{result.reasoning}</ReactMarkdown>
                </CardContent>
              </Card>
            )}

            {hasContent(result.patch) && (
              <Card>
                <CardHeader>
                  <CardTitle>Generated Patch</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto rounded bg-gray-100 p-4 text-xs dark:bg-gray-800 dark:text-gray-100">
                    <ReactMarkdown components={markdownComponents}>{result.patch}</ReactMarkdown>
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