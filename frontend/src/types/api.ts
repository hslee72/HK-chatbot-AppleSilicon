export interface Tenant {
  id: string;
  name: string;
  description: string;
  created_at: string;
}

export interface DocumentMeta {
  title: string;
  summary: string;
  page_count: number;
  filename: string;
  ingested_at: string;
  error?: string;
}

export interface Citation {
  source: string;
  page: number;
  text: string;
  score: number | null;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  citations?: Citation[];
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
}

export interface IngestResponse {
  status: string;
  ingested: number;
  total_nodes?: number;
  collection?: string;
  documents: DocumentMeta[];
}

export interface AvailableFile {
  filename: string;
  size_mb: number;
}

export interface HealthStatus {
  status: string;
  ollama: {
    connected: boolean;
    base_url: string;
    models: string[];
  };
}
