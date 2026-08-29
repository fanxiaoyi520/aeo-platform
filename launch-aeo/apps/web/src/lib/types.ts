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
