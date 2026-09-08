"""AEO Platform shared types, errors, and utilities."""

from aeo_shared.ads_inventory_linkage import (
    AdsInventoryLinkage,
    LinkageRecommendation,
    StockStatus,
)
from aeo_shared.after_sales_scripts import (
    AfterSalesScript,
    ScriptLibrary,
    get_script_library,
)
from aeo_shared.agent_catalog import build_default_registry, get_default_registry
from aeo_shared.agent_registry import (
    AgentCapability,
    AgentCategory,
    AgentDeclaration,
    AgentRegistry,
    RiskLevel,
)
from aeo_shared.batch_metrics import (
    AgentExecRecord,
    BatchMetricsAggregator,
    KpiTarget,
    SkuBatchResult,
)
from aeo_shared.budget_optimizer import (
    BudgetAllocation,
    BudgetOptimizer,
    ROIProjection,
    WhatIfResult,
)
from aeo_shared.competitor_monitor import (
    ListingChange,
    ListingSnapshot,
    MonitorDiff,
    compute_diff,
)
from aeo_shared.content_templates import (
    ContentTemplate,
    ContentTemplateLibrary,
    get_content_template_library,
)
from aeo_shared.cron_parser import CronSchedule, matches, next_run, parse_cron
from aeo_shared.cron_scheduler import CronJob, CronScheduler, CronSchedulerConfig
from aeo_shared.dashboard import DashboardService, compute_automation_rate, get_dashboard_service
from aeo_shared.escalation import EscalationEvaluator, EscalationResult, EscalationRule
from aeo_shared.final_acceptance import (
    AcceptanceResult,
    BizKpi,
    FinalAcceptanceReport,
    compute_final_acceptance,
)
from aeo_shared.graph_catalog import (
    SubGraphDefinition,
    build_graph_catalog,
    get_graph_catalog,
    get_subgraph,
)
from aeo_shared.metrics_sdk import (
    AdSpendMetricRecord,
    BusinessMetricsSnapshot,
    OrderMetricRecord,
    build_daily_snapshot,
    compute_gmv,
    compute_roi,
    parse_money,
)
from aeo_shared.multi_graph import MultiGraphOrchestrator, ParentTask, ParentTaskStatus
from aeo_shared.order_ingest import OrderIngestService, UnifiedOrderRecord
from aeo_shared.risk_dsl import (
    RiskAction,
    RiskCondition,
    RiskDecision,
    RiskEffect,
    RiskRule,
    RiskRuleSet,
    default_production_rule_set,
    evaluate_action,
)
from aeo_shared.risk_review import (
    IncidentRecord,
    IncidentType,
    RiskReviewReport,
    TuningSuggestion,
    analyze_incidents,
    build_review_report,
    classify_incidents,
    generate_tuning_suggestions,
)
from aeo_shared.roi_comparison import (
    CostBaseline,
    PlatformReport,
    RoiComparisonReport,
    build_full_report,
    build_platform_report,
    compute_roi_comparison,
)
from aeo_shared.selection_scoring import (
    CompetitorData,
    SelectionInput,
    SelectionResult,
    score_product,
)
from aeo_shared.strategy_task_creator import (
    ActionMapping,
    ActionMappingEntry,
    StrategyTaskCreator,
    get_action_mapping,
)
from aeo_shared.task_scheduler import (
    AgentTaskScheduler,
    ScheduledAgentTask,
    ScheduledTaskStatus,
    SchedulerConfig,
    TaskPriority,
)
from aeo_shared.trial_monitor import (
    HealthStatus,
    TrialMonitor,
    TrialRecord,
    TrialStatus,
    compute_availability,
    compute_p95_latency,
    compute_recovery_time,
)

__all__ = [
    "ActionMapping",
    "ActionMappingEntry",
    "AdsInventoryLinkage",
    "AfterSalesScript",
    "AgentCapability",
    "AgentCategory",
    "AgentDeclaration",
    "AgentExecRecord",
    "AgentRegistry",
    "AgentTaskScheduler",
    "BatchMetricsAggregator",
    "BudgetAllocation",
    "BudgetOptimizer",
    "CompetitorData",
    "ContentTemplate",
    "ContentTemplateLibrary",
    "CostBaseline",
    "CronJob",
    "CronSchedule",
    "CronScheduler",
    "CronSchedulerConfig",
    "DashboardService",
    "EscalationEvaluator",
    "EscalationResult",
    "EscalationRule",
    "IncidentRecord",
    "IncidentType",
    "KpiTarget",
    "ListingChange",
    "ListingSnapshot",
    "LinkageRecommendation",
    "MonitorDiff",
    "MultiGraphOrchestrator",
    "OrderIngestService",
    "OrderMetricRecord",
    "ParentTask",
    "ParentTaskStatus",
    "AdSpendMetricRecord",
    "BusinessMetricsSnapshot",
    "PlatformReport",
    "RiskLevel",
    "RiskAction",
    "RiskCondition",
    "RiskDecision",
    "RiskEffect",
    "RiskRule",
    "RiskRuleSet",
    "RiskReviewReport",
    "ROIProjection",
    "RoiComparisonReport",
    "ScheduledAgentTask",
    "ScheduledTaskStatus",
    "SchedulerConfig",
    "ScriptLibrary",
    "SelectionInput",
    "SelectionResult",
    "SkuBatchResult",
    "StockStatus",
    "SubGraphDefinition",
    "TaskPriority",
    "TuningSuggestion",
    "UnifiedOrderRecord",
    "WhatIfResult",
    "HealthStatus",
    "TrialMonitor",
    "TrialRecord",
    "TrialStatus",
    "BizKpi",
    "AcceptanceResult",
    "FinalAcceptanceReport",
    "analyze_incidents",
    "build_daily_snapshot",
    "build_default_registry",
    "build_full_report",
    "build_graph_catalog",
    "build_platform_report",
    "build_review_report",
    "classify_incidents",
    "compute_diff",
    "compute_gmv",
    "compute_roi",
    "compute_roi_comparison",
    "compute_automation_rate",
    "compute_availability",
    "compute_p95_latency",
    "compute_recovery_time",
    "compute_final_acceptance",
    "default_production_rule_set",
    "evaluate_action",
    "generate_tuning_suggestions",
    "matches",
    "next_run",
    "parse_cron",
    "parse_money",
    "get_default_registry",
    "get_graph_catalog",
    "get_script_library",
    "get_subgraph",
    "get_content_template_library",
    "get_dashboard_service",
    "get_action_mapping",
    "score_product",
    "StrategyTaskCreator",
]
