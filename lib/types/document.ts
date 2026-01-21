export interface LegalDocument {
  id: string;
  title: string;
  content: string;
  category: "case-law" | "statute" | "regulation" | "article";
  jurisdiction: string;
  date: Date;
  source: string;
  metadata: DocumentMetadata;
}

export interface DocumentMetadata {
  court?: string;
  judges?: string[];
  parties?: string[];
  citations?: string[];
  keywords?: string[];
}
