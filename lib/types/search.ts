import { LegalDocument } from "./document";

export interface SearchQuery {
  query: string;
  filters?: SearchFilters;
  options?: SearchOptions;
}

export interface SearchFilters {
  category?: string[];
  jurisdiction?: string[];
  dateRange?: { start: Date; end: Date };
}

export interface SearchOptions {
  limit?: number;
  offset?: number;
  sortBy?: "relevance" | "date";
}

export interface SearchResult {
  id: string;
  document: LegalDocument;
  score: number;
  highlights: string[];
  reasoning?: string;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  processingTime: number;
}
