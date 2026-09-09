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

export type AgentCapability = {
  name: string;
  description: string;
  tools: string[];
};

export type AgentCatalogItem = {
  agent_id: string;
  display_name: string;
  category: string;
  description: string;
  version: string;
  capabilities: AgentCapability[];
  risk_level: string;
  platforms: string[];
  status: string;
  graph_node: string | null;
  timeout_seconds: number;
};

export type SubGraphSummary = {
  graph_id: string;
  display_name: string;
  description: string;
  category: string;
  agent_ids: string[];
  step_count: number;
};

export type AgentCommandConsole = {
  agents: AgentCatalogItem[];
  graphs: SubGraphSummary[];
  summary: {
    total: number;
    active: number;
    planned: number;
  };
};

export type DashboardTrendEntry = {
  date: string;
  gmv: string;
  roi: string | null;
  order_count: number;
  automation_rate: string | null;
};

export type DashboardData = {
  gmv: string;
  roi: string | null;
  ad_spend: string;
  order_count: number;
  automation_rate: string | null;
  trend: DashboardTrendEntry[];
  period_days: number;
};

export type DTCStorefront = {
  total_products: number;
  active_products: number;
  total_orders: number;
  paid_orders: number;
  low_stock_items: number;
  active_discounts: number;
};

export type DTCKpis = {
  avg_conversion_rate: number | null;
  avg_cart_abandonment_rate: number | null;
  avg_order_value: number | null;
  total_revenue: string;
  total_sessions: number;
  total_orders: number;
  customer_lifetime_value: string | null;
  repeat_purchase_rate: string | null;
  email_marketing_opt_in_rate: string | null;
  metric_days: number;
  customer_count: number;
  abandoned_cart_count: number;
};

export type DTCAbandonedCartsSummary = {
  total: number;
  recovery_email_sent: number;
  total_value: string;
};

export type DTCDashboardData = {
  storefront: DTCStorefront;
  kpis: DTCKpis;
  recent_orders: Record<string, unknown>[];
  top_products: Record<string, unknown>[];
  abandoned_carts_summary: DTCAbandonedCartsSummary;
};
