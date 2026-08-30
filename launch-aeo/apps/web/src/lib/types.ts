export type ApiEnvelope<T> = {
  code: number;
  message: string;
  data: T;
  request_id: string;
};

export type KnowledgeStats = {
  total_chunks: number;
};

export type KnowledgeSearchResult = {
  doc_id: string;
  content: string;
  score: number;
  category: string;
  platform: string;
  source_file: string;
  chunk_index: number;
};

export type KnowledgeSearchResponse = {
  query: string;
  results: KnowledgeSearchResult[];
  total: number;
};

export type KnowledgeReindexResponse = {
  documents: number;
  chunks: number;
  total: number;
};

export type KnowledgeDocumentItem = {
  source_file: string;
  size_bytes: number;
  extension: string;
  updated_at: string;
};

export type KnowledgeDocumentsResponse = {
  items: KnowledgeDocumentItem[];
  total: number;
};

export type KnowledgeUploadResponse = {
  source_file: string;
  size_bytes: number;
  category: string;
  reindex: KnowledgeReindexResponse;
};

export type KnowledgeDocumentItem = {
  source_file: string;
  size_bytes: number;
  extension: string;
  updated_at: string;
};

export type KnowledgeDocumentsResponse = {
  items: KnowledgeDocumentItem[];
  total: number;
};

export type KnowledgeUploadResponse = {
  source_file: string;
  size_bytes: number;
  category: string;
  reindex: KnowledgeReindexResponse;
};

export type TaskPlatform = "amazon" | "tiktok";

export type Task = {
  id: string;
  sku: string;
  platform: TaskPlatform | string;
  market: string;
  status: string;
  product_info: Record<string, unknown>;
  trace: unknown[];
  generated?: Record<string, unknown> | null;
  final_output: Record<string, unknown> | null;
  error_message: string | null;
  created_at: string | null;
  updated_at: string | null;
};

export type TaskList = {
  items: Task[];
  total: number;
  page: number;
  page_size: number;
};

export type CreateTaskPayload = {
  sku: string;
  platform: TaskPlatform;
  market?: string;
  product_info?: {
    competitor_asins?: string[];
    keywords?: string[];
  };
};
