"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

interface SearchResult {
  id: string;
  title: string;
  category: string;
  jurisdiction: string;
  snippet: string;
}

interface ResultsListProps {
  results: SearchResult[];
}

export default function ResultsList({ results }: ResultsListProps) {
  if (results.length === 0) {
    return (
      <Card>
        <CardContent className="flex h-48 items-center justify-center">
          <p className="text-muted-foreground">
            No results found. Try a different search query.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {results.map((result) => (
        <Card key={result.id}>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-lg">{result.title}</CardTitle>
                <CardDescription>
                  {result.category} • {result.jurisdiction}
                </CardDescription>
              </div>
              <Button variant="outline" size="sm">
                View
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{result.snippet}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
