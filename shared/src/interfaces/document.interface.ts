/**
 * Document types supported by the platform
 */
export enum DocumentType {
  PDF = 'pdf',
  DOCX = 'docx',
  TXT = 'txt',
  HTML = 'html',
  JSON = 'json',
}

/**
 * Document processing status
 */
export enum DocumentStatus {
  PENDING = 'pending',
  PROCESSING = 'processing',
  COMPLETED = 'completed',
  FAILED = 'failed',
}

/**
 * Core document structure
 */
export interface Document {
  id: string;
  title: string;
  type: DocumentType;
  status: DocumentStatus;
  content?: string;
  metadata: DocumentMetadata;
  createdAt: Date;
  updatedAt: Date;
}

/**
 * Document metadata
 */
export interface DocumentMetadata {
  author?: string;
  jurisdiction?: string;
  courtLevel?: string;
  caseNumber?: string;
  fileSize?: number;
  pageCount?: number;
  tags?: string[];
  [key: string]: unknown;
}

/**
 * Document ingestion request
 */
export interface DocumentIngestionRequest {
  file: Buffer | string;
  fileName: string;
  type: DocumentType;
  metadata?: Partial<DocumentMetadata>;
}

/**
 * Document search query
 */
export interface DocumentSearchQuery {
  query: string;
  filters?: DocumentSearchFilters;
  limit?: number;
  offset?: number;
}

/**
 * Document search filters
 */
export interface DocumentSearchFilters {
  type?: DocumentType[];
  jurisdiction?: string[];
  dateRange?: {
    start: Date;
    end: Date;
  };
  tags?: string[];
}

/**
 * Document search result
 */
export interface DocumentSearchResult {
  documents: Document[];
  total: number;
  hasMore: boolean;
}
