# MV1-09 Acceptance Report: 3 Agent Chain + Audit Trail

> **Date:** 2026-09-01
> **Task:** MV1-09 — MV1 生产验收：3 Agent 联调 + 沙箱店审计全记录
> **Status:** PASS

---

## 1. Acceptance Criteria

MV1-09 verifies the production-readiness of the listing agent chain:

| # | Criterion | Source |
|---|-----------|--------|
| AC-1 | generate → compliance → review 三 Agent 联调通过 | `10_MANAGER_VISION_PLAN.md` |
| AC-2 | 每个 Agent 产生可查询的 trace 事件 | M03 §6 / MS3 acceptance |
| AC-3 | compliance_agent 检测违规并尝试 auto-fix | M03 §5 |
| AC-4 | review_agent 持久化 listing version | M03 §5 |
| AC-5 | 全链路 trace 包含 agent / status / timestamp | audit trail spec |

---

## 2. Test Results

```
apps/orchestrator/tests/test_mv1_acceptance.py — 7/7 passed

TestMV1_09_ThreeAgentChain:
  PASS  test_generate_agent_produces_valid_listing
  PASS  test_compliance_agent_validates_listing
  PASS  test_compliance_agent_detects_and_fixes_forbidden_phrases
  PASS  test_review_agent_persists_listing
  PASS  test_full_chain_generate_compliance_review

TestMV1_09_AuditTrail:
  PASS  test_trace_events_have_required_fields
  PASS  test_chain_produces_queryable_trace
```

### Full Suite Regression

```
280 passed, 0 failed
Coverage: 85.77% (threshold: 70%)
Lint: ruff check clean, ruff format clean
Types: mypy clean (0 errors)
```

---

## 3. Chain Flow Verification

```
state (initial)
  │
  ▼
generate_node ──→ LLM produces title/bullets/search_terms/description
  │               trace: generate_agent STARTED → COMPLETED
  ▼
compliance_node ──→ validate_generated() checks forbidden phrases, length, bullet count
  │                 auto-fix: strip HTML, remove forbidden phrases, truncate
  │                 trace: compliance_agent STARTED → COMPLETED/FAILED
  ▼
review_node ──→ save_listing_version() persists to storage
  │             final_output = generated + metrics + listing_version_id
  │             trace: review_agent STARTED → COMPLETED
  ▼
TaskStatus.COMPLETED
```

### Key Assertions

- **generate**: title non-empty, exactly 5 bullets, platform = "amazon"
- **compliance**: valid listing passes; forbidden phrases ("BEST", "free shipping") detected and removed
- **review**: final_output contains title, metrics.listing_version non-null, status = COMPLETED
- **full chain**: all 3 agents appear in accumulated trace; compliance passes after generate
- **audit trail**: every trace event has agent, status, timestamp fields

---

## 4. Risk Level Coverage

The 3-agent chain covers L0 and L1 risk levels:

| Agent | Risk Level | Behavior |
|-------|-----------|----------|
| research_agent | L0 | Auto-allow (read-only) |
| rules_agent | L0 | Auto-allow (read-only) |
| generate_agent | L0 | Auto-allow (draft, no external effect) |
| compliance_agent | L1 | Validation gate (auto-fix + retry loop) |
| human_review | L1 | HITL interrupt (approve/reject) |
| review_agent | L0 | Finalize (persist after HITL approval) |

L2 (deny) actions are handled by the risk engine (MV1-05) before reaching the chain.

---

## 5. Artifacts

| File | Description |
|------|-------------|
| `apps/orchestrator/tests/test_mv1_acceptance.py` | 7 acceptance tests |

---

## 6. Conclusion

MV1-09 acceptance criteria met. The generate → compliance → review chain:
- Produces valid Amazon listing JSON
- Validates and auto-fixes compliance issues
- Persists listing versions
- Maintains a queryable audit trail across all 3 agents

**Recommendation:** Mark MV1-09 as `completed`.
