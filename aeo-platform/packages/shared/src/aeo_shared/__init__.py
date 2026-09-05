"""AEO Platform shared types, errors, and utilities."""

from aeo_shared.agent_catalog import build_default_registry, get_default_registry
from aeo_shared.agent_registry import (
    AgentCapability,
    AgentCategory,
    AgentDeclaration,
    AgentRegistry,
    RiskLevel,
)
from aeo_shared.competitor_monitor import (
    ListingChange,
    ListingSnapshot,
    MonitorDiff,
    compute_diff,
)
from aeo_shared.cron_parser import CronSchedule, matches, next_run, parse_cron
from aeo_shared.cron_scheduler import CronJob, CronScheduler, CronSchedulerConfig
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
from aeo_shared.selection_scoring import (
    CompetitorData,
    SelectionInput,
    SelectionResult,
    score_product,
)
from aeo_shared.task_scheduler import (
    AgentTaskScheduler,
    ScheduledAgentTask,
    ScheduledTaskStatus,
    SchedulerConfig,
    TaskPriority,
)

__all__ = [
    "AgentCapability",
    "AgentCategory",
    "AgentDeclaration",
    "AgentRegistry",
    "AgentTaskScheduler",
    "CompetitorData",
    "CronJob",
    "CronSchedule",
    "CronScheduler",
    "CronSchedulerConfig",
    "ListingChange",
    "ListingSnapshot",
    "MonitorDiff",
    "MultiGraphOrchestrator",
    "OrderMetricRecord",
    "ParentTask",
    "ParentTaskStatus",
    "AdSpendMetricRecord",
    "BusinessMetricsSnapshot",
    "RiskLevel",
    "RiskAction",
    "RiskCondition",
    "RiskDecision",
    "RiskEffect",
    "RiskRule",
    "RiskRuleSet",
    "ScheduledAgentTask",
    "ScheduledTaskStatus",
    "SchedulerConfig",
    "SelectionInput",
    "SelectionResult",
    "SubGraphDefinition",
    "TaskPriority",
    "build_daily_snapshot",
    "build_default_registry",
    "build_graph_catalog",
    "compute_diff",
    "compute_gmv",
    "compute_roi",
    "default_production_rule_set",
    "evaluate_action",
    "matches",
    "next_run",
    "parse_cron",
    "parse_money",
    "get_default_registry",
    "get_graph_catalog",
    "get_subgraph",
    "score_product",
]
