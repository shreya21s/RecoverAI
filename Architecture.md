# RecoverAI — Complete System Architecture & Workflow Specification
                        ┌─────────────────────────────────┐
                        │   FAILED PAYMENT / BATCH INTAKE │
                        └────────────────┬────────────────┘
                                         │
                                         ▼
                        ┌─────────────────────────────────┐
                        │        1. LOAD CASE NODE        │
                        │ (Retrieve Case, Payment, Cust.) │
                        └────────────────┬────────────────┘
                                         │
                                         ▼
                        ┌─────────────────────────────────┐
                        │       2. SUPERVISOR AGENT       │
                        │  (Validate Context Completeness)│
                        └────────┬───────────────┬────────┘
                                 │               │ [Missing Data]
                        [Valid]  │               └──────────────────────────┐
                                 ▼                                          │
                        ┌─────────────────────────────────┐                 │
                        │       3. DIAGNOSIS AGENT        │                 │
                        │  (Classify Root Cause + Conf.)  │                 │
                        └────────────────┬────────────────┘                 │
                                         │                                  │
                                         ▼                                  │
                        ┌─────────────────────────────────┐                 │
                        │   4. CUSTOMER ANALYSIS AGENT    │                 │
                        │   (Segment, Reliability, LTV)   │                 │
                        └────────────────┬────────────────┘                 │
                                         │                                  │
                                         ▼                                  │
                        ┌─────────────────────────────────┐                 │
                        │        5. STRATEGY AGENT        │                 │
                        │  (Recommend Action & Prob./EV)  │                 │
                        └────────────────┬────────────────┘                 │
                                         │                                  │
                                         ▼                                  │
                        ┌─────────────────────────────────┐                 │
                        │     6. POLICY NODE (ENGINE)     │                 │
                        │  (Evaluate 4-Tier Guardrails)   │                 │
                        └────────────────┬────────────────┘                 │
                                         │                                  │
                                         ▼                                  │
                        ┌─────────────────────────────────┐                 │
                        │   7. EXPLAINABILITY SERVICE     │                 │
                        │ (Factors, Alternatives, Counterf)│                │
                        └────────────────┬────────────────┘                 │
                                         │                                  │
                 ┌───────────────────────┼───────────────────────┐          │
                 │ [APPROVED]            │ [HITL_REQUIRED]       │ [STOPPED/│
                 ▼                       ▼                       │  BLOCKED]│
      ┌─────────────────────┐ ┌─────────────────────┐            │          │
      │ 8. EXECUTION NODE   │ │ 9. HITL PENDING NODE│            │          │
      │ (Lifecycle & Prov.) │ │(Create HumanApproval│            │          │
      └──────────┬──────────┘ └──────────┬──────────┘            │          │
                 │                       │                       │          │
                 │              ┌────────┴────────┐              │          │
                 │              │ Human Reviewer  │              │          │
                 │              └────┬────────┬───┘              │          │
                 │        [Approved] │        │ [Rejected]       │          │
                 │                   ▼        └──────────────┐   │          │
                 │        ┌─────────────────────┐            │   │          │
                 │        │ Pre-Execution Policy│            │   │          │
                 │        │    Revalidation     │            │   │          │
                 │        └─────┬─────────┬─────┘            │   │          │
                 │     [Passed] │         │ [Hard Block]     │   │          │
                 ├──────────────┘         └──────────────┐   │   │          │
                 │                                       │   │   │          │
                 ▼                                       ▼   ▼   ▼          ▼
      ┌─────────────────────┐                 ┌─────────────────────────────┐
      │ 10. PROVIDER DISPATCH│                │      11. FINALIZE NODE      │
      │ (Sim / Future Gtwy) │                 │  (Update Case Terminal State│
      └──────────┬──────────┘                 │   & Log Audit Trail Events) │
                 │                            └──────────────┬──────────────┘
                 ▼                                           │
      ┌─────────────────────┐                                │
      │ 12. RECOVERY OUTCOME│────────────────────────────────┘
      │(RECOVERED/SCHEDULED/│
      │ PROCESSING/FAILED)  │
      └─────────────────────┘
