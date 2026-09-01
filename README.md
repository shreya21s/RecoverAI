# RecoverAI

### AI-powered revenue recovery with policy-controlled execution.

**Philosophy**: 
* **AI recommends.**
* **Policy decides.**
* **Humans handle exceptions.**
* **RecoverAI measures the outcome.**

---

## 1. Problem Statement
Failed payments create massive revenue loss. However, blindly retrying payments is highly problematic: it degrades customer experiences, causes repeated failures, creates unnecessary execution costs, and raises serious compliance/risk flags.

## 2. Solution: RecoverAI
RecoverAI solves this by analyzing failed payments using specialized AI agents, selecting optimized recovery strategies, evaluating them through a deterministic Policy Engine before execution, routing sensitive cases to humans, executing only approved actions, and measuring the actual revenue recovered across batches against benchmark simulations.

---

## 3. System Architecture Diagram

```text
                    Failed Payment
                           │
                           ▼
                   Supervisor Agent
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
   Diagnosis Agent   Customer Agent   Strategy Agent
   (Failure reason)  (Segment/Risk)   (Strategy recommendation)
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                    Policy Engine
                (Deterministic check)
                           │
             ┌─────────────┼─────────────┐
             ▼             ▼             ▼
          Execute        HITL          Stop
             │             │             │
             ▼             ▼             ▼
          Recovery     Revalidate      Safe State
          Succeeded      Outcome       No execution
             │             │             │
             └─────────────┼─────────────┘
                           ▼
                     Batch Metrics
             (Incremental revenue comparison)
                           │
                           ▼
                     Audit Trail
            (Chronological compliance log)
```


## 4. Recovery Provider Abstraction

RecoverAI separates recovery intelligence from provider-specific execution using a decoupled execution layer:

```text
RecoverAI Decision Engine (LangGraph Agents)
           ↓
     Policy Layer (Deterministic Safeguards)
           ↓
   Recovery Execution Service (Lifecycle, Idempotency, Validation)
           ↓
     Provider Adapter (Unified Interface)
     ├── Simulated Recovery Provider (Local seed & deterministic simulation)
     └── Future Payment Provider Adapter (Integration ready placeholder)
```

* **Standardized Interface**: Standardizes attempt statuses (`REQUESTED`, `VALIDATED`, `DISPATCHED`, `PROCESSING`, `SUCCEEDED`, `FAILED`, `BLOCKED`, `CANCELLED`) and response schemas.
* **Simulation Mode by Default**: Runs in safe local simulation mode by default (`SIMULATION_MODE=true` in settings), requiring no real payment gateway credentials.
* **Decoupled Architecture**: Integrating live payment gateways in the future can be done by creating a new provider adapter inheriting from `RecoveryProvider` without modifying any AI reasoning, strategy determination, policy rules, or HITL flows.

---

## 5. Key Features

* **Multi-Stage Recovery Intelligence**: Specialized agents for payment failure diagnosis, customer segmentation profiling, and recovery strategy selection.
* **Deterministic Policy Controls**: A separate, strict policy engine to enforce safety boundaries (disputes, retry counts, amount limits).
* **Human-in-the-Loop (HITL) Queue**: Escalates high-risk cases for reviewer approval, ensuring pre-execution revalidation before dispatch.
* **Explainable Decisions**: Explicitly maps primary decision factors (e.g. Failure Category, Customer segment) indicating positive or negative impact.
* **Counterfactual Analysis**: Indicates what would need to change for blocked or stopped retries to execute automatically.
* **Idempotent Attempt Execution**: Protects against duplicate actions, double clicks, API retries, and network timeouts.
* **Recovery Attempt History**: Persists attempt-level execution history logs detailing timestamps, revalidation results, and outcomes.
* **Batch Processing**: Groups portfolio cases, isolates processing failures, and produces comprehensive impact reports.
* **Mathematically Correct Revenue Metrics**: Tracks exact recovered funds and baseline comparisons.
* **Chronological Audit Trail**: Records event logs to ensure full security and compliance visibility.
* **Simulation Mode**: Safely runs in an environment-honest local simulator by default.

---

## 6. Demo Architecture Core Philosophy

RecoverAI operates under a unified orchestration paradigm:
* **AI Recommends**: The AI agent intelligence layer analyzes context and recommends the best strategy (e.g., SMART_RETRY).
* **Policy Decides**: The deterministic policy engine acts as an independent authority. It determines whether the action is allowed (APPROVED), stopped (STOPPED), or requires human review (HITL_REQUIRED).
* **Humans Handle Exceptions**: Manual reviewers approve or reject escalations in the Human Review queue. Bypassed soft rules are revalidated during dispatch.

---

## 7. Decision Intelligence & Explainability
RecoverAI implements a deterministic, multi-modal explainability framework to audit and explain every recovery action:
* **AI Recommendation vs. Policy Decision**: The UI explicitly separates the AI intelligence layer's recommendation from the deterministic safety constraints enforced by the Policy Engine.
* **Primary Decision Factors**: Analyzes 5 key signals (Failure Category, Customer Quality, Transaction Amount, Retries, and Recovery Probability) to indicate positive, negative, or neutral impact.
* **Alternative Strategies**: Audits which alternative recovery strategies were considered and why they were not chosen.
* **Counterfactual Analysis**: Computes what would need to change (using real system/policy thresholds) for a stopped or escalated case to be eligible for automatic execution.
* **Batch-Level Explanations**: Aggregates top STOP/HITL policy rules and provides an AI vs. Policy disagreement analysis.
* **Audit Trail Integration**: Automatically logs a `DECISION_EXPLAINED` event in the audit trail for every completed run.

---

## 8. Showcase Cases & Deterministic Paths
RecoverAI comes seeded with 5 key demo cases demonstrating intelligent decision-making:
* **REC-DEMO-001 (Automatic Succeeded)**: PLATINUM customer, temporary failure ➔ approved strategy `WAIT_AND_RETRY` executes automatically, recovering ₹4,500.
* **REC-DEMO-002 (Normal Succeeded)**: GOLD customer, payment abandonment ➔ approved strategy `SEND_PAYMENT_LINK` executes, recovering ₹2,500.
* **REC-DEMO-003 (Human-in-the-Loop)**: High-value transaction ➔ Policy blocks automatically (`HIGH_VALUE_TRANSACTION`). Stays in pending queue until approved, triggering policy revalidation before executing.
* **REC-DEMO-004 (Hard Stop)**: Repeated failures ➔ Policy enforces immediate stop (`MAX_RETRIES_EXCEEDED`) preventing further action.
* **REC-DEMO-005 (Dispute Safeguard)**: Active chargeback ➔ Policy blocks action (`ACTIVE_DISPUTE`) and escalates to human review.

---

## 9. Technology Stack
* **Backend**: FastAPI, SQLAlchemy (SQLite), Pydantic, LangGraph / LangChain, LangSmith.
* **Frontend**: React + Vite, Custom CSS glassmorphic stylesheet, Lucide Icons.

---

## 10. Setup & Execution Instructions

### A. Run Backend
1. Navigate to the backend folder:
   ```bash
   cd backend
   ```
2. Create and activate a python virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   .\venv\Scripts\Activate.ps1
   # Mac/Linux:
   source venv/bin/activate
   ```
3. Install packages:
   ```bash
   pip install -r requirements.txt
   ```
4. Copy environment config:
   ```bash
   cp .env.example .env
   ```
5. Start development API server:
   ```bash
   uvicorn app.main:app --reload
   ```

### B. Run Frontend
1. Navigate to the frontend folder:
   ```bash
   cd frontend
   ```
2. Install node packages:
   ```bash
   npm install
   ```
3. Run development client:
   ```bash
   npm run dev
   ```
4. Open the dashboard in your browser at `http://localhost:5173/`.

### C. Run Backend Tests
To run the full test suite verifying agents, policies, HITL queue actions, and batches:
```bash
cd backend
.\venv\Scripts\python -m pytest
```
