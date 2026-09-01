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

export type RiskLevel = "L0" | "L1" | "L2";
export type RiskEffect = "allow" | "require_hitl" | "deny";

export type RiskRule = {
  rule_id: string;
  action: string;
  risk_level: RiskLevel;
  effect: RiskEffect;
  description: string;
  priority: number;
};

export type RiskRuleSet = {
  version: string;
  rules: RiskRule[];
};

export type RiskDecision = {
  allowed: boolean;
  effect: RiskEffect;
  risk_level: RiskLevel;
  rule_id: string;
  message: string;
};

export type RiskAuditItem = {
  id: string;
  action: string;
  actor: string;
  detail: {
    action: string;
    context: Record<string, unknown>;
    effect: RiskEffect;
    risk_level: RiskLevel;
    rule_id: string;
    message: string;
    allowed: boolean;
  } | null;
  created_at: string;
};

export type RiskAuditListResponse = {
  items: RiskAuditItem[];
  total: number;
};

export type RiskEvaluateRequest = {
  action: string;
  context?: Record<string, unknown>;
};
