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

export type AuthUser = {
  id: string;
  email: string;
  display_name: string | null;
  role: string;
  tenant_id: string;
};

export type AuthSession = {
  access_token: string;
  refresh_token: string;
  user: AuthUser;
};

export type TenantInfo = {
  id: string;
  name: string;
  slug: string;
  plan: string;
  is_active: boolean;
  created_at: string;
};

export type TenantQuota = {
  plan: string;
  description: string;
  tasks: {
    used: number;
    limit: number | null;
    remaining: number | null;
    exceeded: boolean;
  };
  users: {
    limit: number;
  };
};

export type RiskLevel = "L0" | "L1" | "L2";
export type RiskEffect = "allow" | "require_hitl" | "deny";

export type RiskCondition = {
  field: string;
  operator: string;
  value: unknown;
};

export type RiskRule = {
  rule_id: string;
  action: string;
  risk_level: RiskLevel;
  effect: RiskEffect;
  description: string;
  conditions: RiskCondition[];
  priority: number;
};

export type RiskRuleSet = {
  version: string;
  rules: RiskRule[];
  summary: Record<RiskLevel, number>;
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
  created_at: string;
  detail: Record<string, unknown> | null;
};

export type RiskAuditListResponse = {
  items: RiskAuditItem[];
  total: number;
};

export type RiskEvaluateRequest = {
  action: string;
  context?: Record<string, unknown>;
  actor?: string;
};
