# LLM EvalOps (LLMOps Studio) — Frontend Repository Audit & Backend Implementation Specification

---

## 1. Executive Summary

This document presents a comprehensive, evidence-based repository audit of the existing **LLMOps Studio** frontend application and defines the complete backend architectural specification required for production-grade implementation.

The primary objective of LLMOps Studio is to provide AI engineers with an automated, reproducible platform to answer the core operational question:

> _"I changed my model, prompt, or configuration. Did the system actually improve, or did I silently introduce regressions?"_

### Primary Findings

- **Frontend Readiness**: The existing frontend is built with **React 19 + TypeScript + Vite + TanStack Start (Nitro SSR)**. It features a complete design system, dark/light theme, dashboard, dataset management, versioned prompt/model configuration, evaluation launcher, searchable experiment history, detailed case inspection, automated regression comparison, and workspace settings.
- **Service Abstraction**: All page components consume a centralized API service layer in `src/api/*` backed by React Query (`@tanstack/react-query`) and deterministic mock data (`src/mocks/data.ts`).
- **Backend Task**: The backend will be a **modular monolithic FastAPI application in Python**, using **PostgreSQL + SQLAlchemy** as the source of truth, integrating **Groq** and **Google Gemini** LLM gateways, and exposing RESTful endpoints compatible with the existing frontend data structures.

---

## 2. Actual Repository Architecture

### Technology Stack Discovered

- **Core Framework**: React 19 (`react@^19.2.0`), TypeScript (`typescript@^5.8.3`).
- **Build System & SSR**: Vite (`vite@^8.1.5`), `@tanstack/react-start` (`^1.168.32`), `@tanstack/router-plugin` (`^1.168.23`), Nitro SSR (`nitro@3.0.260603-beta`).
- **Routing**: File-based TanStack Router (`@tanstack/react-router@^1.170.18`), auto-generated route tree `src/routeTree.gen.ts`.
- **State Management & Data Fetching**: TanStack React Query (`@tanstack/react-query@^5.101.1`) with centralized query keys and client cache invalidation.
- **UI Components & Icons**: Radix UI primitives (`@radix-ui/react-*`), Lucide icons (`lucide-react@^0.575.0`), Tailwind CSS v4 (`@tailwindcss/vite@^4.2.1`), `class-variance-authority`, `clsx`, `tailwind-merge`.
- **Charts & Visualization**: Recharts (`recharts@^2.15.4`) for area, line, and bar charts.
- **Notifications**: Sonner (`sonner@^2.0.7`).
- **Form & Validation**: `react-hook-form@^7.71.2`, `@hookform/resolvers@^5.2.2`, `zod@^3.24.2`.

### Concise Repository Tree (Architecturally Relevant Files)

```text
llm-guard-main/
├── package.json                          # Scripts & dependencies (React 19, TanStack Router, Recharts)
├── vite.config.ts                        # Vite build configuration with TanStack Start plugin
├── tsconfig.json                         # Strict TypeScript configuration
├── src/
│   ├── api/                              # Centralized API service layer
│   │   ├── client.ts                     # Generic request runner & ApiError handler
│   │   ├── configurations.ts             # Model & Prompt configuration API client
│   │   ├── datasets.ts                   # Dataset CRUD & case management API client
│   │   ├── evaluations.ts                # Simulated progress & evaluation launch API client
│   │   ├── experiments.ts                # Experiment list, detail, & dashboard summary API client
│   │   ├── regressions.ts                # Regression comparison API client
│   │   └── settings.ts                   # Workspace settings & threshold policy API client
│   ├── components/                       # Shared & Domain-specific UI components
│   │   ├── common/                       # MetricCard, PageHeader, ProviderBadge, States, StatusBadge
│   │   ├── experiments/                  # ExperimentTable, CaseDetailDrawer
│   │   ├── layout/                       # AppSidebar, TopBar
│   │   ├── regression/                   # MetricComparisonTable
│   │   ├── ui/                           # Radix UI wrapper primitives (button, dialog, input, etc.)
│   │   └── theme-provider.tsx            # Dark/Light theme context
│   ├── lib/                              # Core domain algorithms & helpers
│   │   ├── regression.ts                 # Regression logic engine (computeComparison)
│   │   ├── error-capture.ts              # UI error boundary handling
│   │   └── utils.ts                      # Tailwind cn class merging helper
│   ├── mocks/                            # Deterministic mock data generator
│   │   └── data.ts                       # Datasets, cases, configurations, seeds, breakdown logic
│   ├── routes/                           # TanStack Router page views
│   │   ├── __root.tsx                    # Root layout with AppSidebar, TopBar, & Toaster
│   │   ├── index.tsx                     # Dashboard (/ route)
│   │   ├── datasets.index.tsx            # Datasets overview (/datasets)
│   │   ├── datasets.$datasetId.tsx       # Dataset details & case table (/datasets/$datasetId)
│   │   ├── configurations.tsx            # Model & Prompt config management (/configurations)
│   │   ├── evaluations.new.tsx           # Launch evaluation run (/evaluations/new)
│   │   ├── experiments.index.tsx         # Experiment history (/experiments)
│   │   ├── experiments.$experimentId.tsx # Experiment results & case inspection (/experiments/$experimentId)
│   │   ├── regression.tsx                # Regression comparison & promotion gate (/regression)
│   │   └── settings.tsx                  # Workspace settings (/settings)
│   ├── types/                            # Domain TypeScript interfaces
│   │   └── index.ts                      # Dataset, Experiment, RegressionComparison, Settings types
│   ├── utils/                            # Formatting helpers
│   │   └── format.ts                     # formatPercent, formatLatency, formatCost, formatTokens
│   ├── routeTree.gen.ts                  # Auto-generated TanStack route tree
│   └── router.tsx                        # Router initialization & QueryClient instance
```

---

## 3. Frontend Page Audit

| Route / Path                                | Main Purpose                                          | Main Components Used                                                                             | Primary Data Displayed                                                                                                                                                                                                          | Current Data Source                                                                                                        | Key User Actions & Controls                                                                                                                              | Navigation Target                                                               |
| :------------------------------------------ | :---------------------------------------------------- | :----------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------ |
| **`/`** (Dashboard)                         | Workspace health overview                             | `MetricCard`, `ChartCard` (Recharts), `ExperimentTable`, `StatusBadge`, `PageHeader`             | Total experiments, weekly evals, avg quality, avg latency, total cost, regression pass rate, quality/latency/cost charts over time, recent experiments, regression alerts                                                       | `getDashboardSummary()` in `src/api/experiments.ts` via React Query                                                        | View all experiments, open regression check, click alert link                                                                                            | `/evaluations/new`, `/regression`, `/experiments`, `/experiments/$experimentId` |
| **`/datasets`** (Datasets List)             | View & create evaluation datasets                     | `Table`, `Dialog`, `Input`, `Textarea`, `Pill`, `Button`, `PageHeader`                           | Dataset name, description, case count, category tags, created/updated dates                                                                                                                                                     | `listDatasets()` in `src/api/datasets.ts`                                                                                  | "New Dataset" modal (parse pipe-delimited input \| expected \| category lines), open dataset                                                             | `/datasets/$datasetId`, `/evaluations/new`                                      |
| **`/datasets/$datasetId`** (Dataset Detail) | Inspect test cases in a dataset                       | `Table`, `MetricCard`, `Input`, `Select`, `Dialog`, `Button`, `PageHeader`                       | Dataset metadata, total cases, category breakdown, case list table (input, expected, category, metadata)                                                                                                                        | `getDatasetDetail()` in `src/api/datasets.ts`                                                                              | Search cases, filter by category, "Add Case" modal, back button                                                                                          | `/datasets`                                                                     |
| **`/configurations`** (Configurations)      | Manage LLM model & prompt settings                    | `Tabs`, `Table`, `Dialog`, `Input`, `Textarea`, `Select`, `ProviderBadge`, `PromptStatusBadge`   | Model configs table (provider, model, temp, max_tokens); Prompt configs table (name, status, version history, system prompt, user template)                                                                                     | `listModelConfigurations()`, `listPromptConfigurations()`, `getSettings()` in `src/api/configurations.ts`                  | "New Model Config" modal, "New Prompt" modal, "Add Version" modal, view version history dialog                                                           | `/evaluations/new`                                                              |
| **`/evaluations/new`**                      | Configure and execute evaluation runs                 | `Progress`, `Checkbox`, `Input`, `Select`, `Button`, `PageHeader`                                | Dataset selector, Model config selector, Prompt & version selector, metric checkboxes, progress bar                                                                                                                             | `listDatasets()`, `listModelConfigurations()`, `listPromptConfigurations()`, `runEvaluation()` in `src/api/evaluations.ts` | Select dataset/model/prompt/version, check/uncheck metrics, click "Run Evaluation" (simulates 4-stage progress)                                          | `/experiments/$experimentId` upon completion                                    |
| **`/experiments`**                          | Searchable history of evaluation runs                 | `ExperimentTable`, `Input`, `Select`, `Button`, `PageHeader`                                     | Filterable experiment runs table (name, dataset, model, prompt, quality, pass rate, latency, tokens, cost, regression status)                                                                                                   | `listExperiments()` in `src/api/experiments.ts`                                                                            | Search text filter, dataset dropdown, provider dropdown, model dropdown, version dropdown, status dropdown, date filter, select 2 rows & click "Compare" | `/regression?baseline=A&candidate=B`, `/experiments/$experimentId`              |
| **`/experiments/$experimentId`**            | Detailed results for single experiment                | `MetricCard`, `BarChart` (Recharts), `Table`, `CaseDetailDrawer`, `ProviderBadge`, `StatusBadge` | Quality, pass rate, avg/p95 latency, tokens, cost; Metric breakdown bar chart; Category performance chart; Case results table                                                                                                   | `getExperimentResult()` in `src/api/experiments.ts`                                                                        | Click case row to open `CaseDetailDrawer` (side-by-side input, expected, model output, metric scores, failure reason), click "Compare for regressions"   | `/regression?candidate=$experimentId`                                           |
| **`/regression`**                           | Baseline vs candidate comparison & promotion decision | `MetricComparisonTable`, `MetricCard`, `Table`, `Dialog`, `StatusBadge`, `Pill`, `Button`        | Baseline/candidate experiment selector, PASS/FAIL verdict banner, PROMOTION GATE: PASSED/BLOCKED badge, 6 gate rules, failure explanations list, metric comparison table, category performance, regressed cases, improved cases | `compareExperiments()` in `src/api/regressions.ts` & `computeComparison()` in `src/lib/regression.ts`                      | Select baseline & candidate experiments, click "Swap", click regressed or improved case row to open side-by-side inspection modal                        | `/experiments`, `/experiments/$experimentId`                                    |
| **`/settings`**                             | Workspace defaults & threshold policy                 | `Input`, `Select`, `Checkbox`, `Button`, `Pill`, `PageHeader`                                    | Connected LLM providers (Groq, Gemini) status & model list; Evaluation default metrics, judge model, concurrency slider; Regression max quality/factuality/latency/cost thresholds & critical category zero-tolerance selectors | `getSettings()`, `updateEvaluationDefaults()`, `updateRegressionThresholds()` in `src/api/settings.ts`                     | Edit & save evaluation defaults, edit & save regression thresholds, toggle critical categories                                                           | N/A                                                                             |

---

## 4. Component & Data Flow Analysis

### Core Data Flow Pattern

```text
UI Page Component (React 19)
       ↓ (uses hook)
@tanstack/react-query (useQuery / useMutation)
       ↓ (calls client function)
src/api/*.ts (Service Layer Abstraction)
       ↓ (invokes request helper)
src/api/client.ts (Simulated async request runner with ApiError)
       ↓ (reads/mutates state)
src/mocks/data.ts (Deterministic Mock Data Generator)
```

### Component Inventory

1. **Layout Components**:
   - `AppSidebar.tsx` ([src/components/layout/AppSidebar.tsx](file:///d:/Projects/LLM-Guard/llm-guard-main/src/components/layout/AppSidebar.tsx)): Sticky sidebar navigation with collapse/expand toggle and route highlight.
   - `TopBar.tsx` ([src/components/layout/TopBar.tsx](file:///d:/Projects/LLM-Guard/llm-guard-main/src/components/layout/TopBar.tsx)): Header with breadcrumbs and global search input navigating to `/experiments?q=...`.
2. **Common Domain Components**:
   - `MetricCard.tsx` ([src/components/common/MetricCard.tsx](file:///d:/Projects/LLM-Guard/llm-guard-main/src/components/common/MetricCard.tsx)): Displays summary metric value, label, optional icon, delta badge, and hint text.
   - `PageHeader.tsx` ([src/components/common/PageHeader.tsx](file:///d:/Projects/LLM-Guard/llm-guard-main/src/components/common/PageHeader.tsx)): Page title, description, and action button toolbar.
   - `ProviderBadge.tsx` ([src/components/common/ProviderBadge.tsx](file:///d:/Projects/LLM-Guard/llm-guard-main/src/components/common/ProviderBadge.tsx)): Badge with provider logo/text (`groq` or `gemini`).
   - `StatusBadge.tsx` ([src/components/common/StatusBadge.tsx](file:///d:/Projects/LLM-Guard/llm-guard-main/src/components/common/StatusBadge.tsx)): Regression status (`PASS`, `WARNING`, `FAIL`), Case status (`PASS`, `FAIL`), `Pill`, `PromptStatusBadge`, `RunStatusBadge`.
   - `States.tsx` ([src/components/common/States.tsx](file:///d:/Projects/LLM-Guard/llm-guard-main/src/components/common/States.tsx)): `LoadingState`, `ErrorState`, and `EmptyState` placeholder components.
3. **Experiment Components**:
   - `ExperimentTable.tsx` ([src/components/experiments/ExperimentTable.tsx](file:///d:/Projects/LLM-Guard/llm-guard-main/src/components/experiments/ExperimentTable.tsx)): Selectable table of experiments with checkboxes for regression comparison.
   - `CaseDetailDrawer.tsx` ([src/components/experiments/CaseDetailDrawer.tsx](file:///d:/Projects/LLM-Guard/llm-guard-main/src/components/experiments/CaseDetailDrawer.tsx)): Side sheet drawer displaying case input, expected output, model output, metric scores, failure reason, and judge explanation.
4. **Regression Components**:
   - `MetricComparisonTable.tsx` ([src/components/regression/MetricComparisonTable.tsx](file:///d:/Projects/LLM-Guard/llm-guard-main/src/components/regression/MetricComparisonTable.tsx)): Displays baseline vs candidate metric comparison, difference %, threshold %, and PASS/FAIL/WARNING status.

---

## 5. Mock Data Audit

All mock data is centralized in [src/mocks/data.ts](file:///d:/Projects/LLM-Guard/llm-guard-main/src/mocks/data.ts) using a deterministic pseudo-random seed generator (`hashSeed` + `mulberry32`).

| Mock Variable Name     | Location                | TypeScript Type                                              | Key Fields                                                                                                                                                                                                                                                                                              | Represented Backend Entity                  | Consuming Pages / Components                                        | Classification       |
| :--------------------- | :---------------------- | :----------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :------------------------------------------ | :------------------------------------------------------------------ | :------------------- |
| `SUPPORT_TEMPLATES`    | `src/mocks/data.ts:44`  | `Partial<Record<EvaluationCategory, { input, expected }[]>>` | `input`, `expected`                                                                                                                                                                                                                                                                                     | Ground truth test case templates            | `buildCases()`, Datasets page                                       | Test case template   |
| `datasets`             | `src/mocks/data.ts:252` | `Dataset[]`                                                  | `id`, `name`, `description`, `case_count`, `categories`, `created_at`, `updated_at`                                                                                                                                                                                                                     | `datasets` table                            | Datasets page (`/datasets`), Dashboard                              | Dataset summary      |
| `datasetDetails`       | `src/mocks/data.ts:310` | `DatasetDetail[]`                                            | `id`, `name`, `description`, `case_count`, `categories`, `cases` (`EvaluationCase[]`)                                                                                                                                                                                                                   | `datasets` + `test_cases` tables            | Dataset detail (`/datasets/$datasetId`), New Evaluation             | Dataset + Cases      |
| `modelConfigurations`  | `src/mocks/data.ts:340` | `ModelConfiguration[]`                                       | `id`, `name`, `provider`, `model`, `temperature`, `max_tokens`, `created_at`                                                                                                                                                                                                                            | `model_configs` table                       | Configurations (`/configurations`), New Evaluation                  | Model Configuration  |
| `promptConfigurations` | `src/mocks/data.ts:380` | `PromptConfiguration[]`                                      | `id`, `name`, `status`, `latest_version`, `versions` (`PromptVersion[]`), `created_at`                                                                                                                                                                                                                  | `prompts` + `prompt_versions` tables        | Configurations (`/configurations`), New Evaluation                  | Prompt Configuration |
| `experimentSeeds`      | `src/mocks/data.ts:462` | `ExperimentSeed[]` (14 experiments: `exp-001` to `exp-014`)  | `id`, `name`, `dataset_id`, `model_config_id`, `prompt_id`, `prompt_version`, `quality_score`, `pass_rate`, `avg_latency_ms`, `p95_latency_ms`, `total_tokens`, `estimated_cost`, `regression_status`, `metric_breakdown`, `category_scores`                                                            | `experiments` + `experiment_results` tables | Dashboard, Experiments (`/experiments`), Regression (`/regression`) | Experiment Run       |
| `settings`             | `src/mocks/data.ts:950` | `Settings`                                                   | `evaluation_defaults` (`default_metrics`, `concurrency`, `judge_model`), `regression_thresholds` (`max_quality_regression_pct`, `max_factuality_regression_pct`, `max_latency_increase_pct`, `max_cost_increase_pct`, `critical_categories`), `providers` (`provider`, `label`, `configured`, `models`) | `settings` table / workspace config         | Settings (`/settings`), New Evaluation, Regression engine           | Workspace Settings   |

---

## 6. TypeScript Data Model Audit

All primary domain interfaces are defined in [src/types/index.ts](file:///d:/Projects/LLM-Guard/llm-guard-main/src/types/index.ts).

### Domain Model Inventory

```text
1. Provider
   Frontend Type: export type Provider = "groq" | "gemini";
   Used By: ModelConfiguration, Experiment, ProviderBadge, ProviderStatus
   Likely Backend Entity: Enum / VARCHAR column in model_configs

2. EvaluationCategory
   Frontend Type: export type EvaluationCategory = "factuality" | "reasoning" | "summarization" | "customer-support" | "instruction-following" | "safety" | "billing" | "technical" | "account-management" | "general";
   Used By: EvaluationCase, Dataset, CategoryRegression, RegressionThresholds
   Likely Backend Entity: Enum / VARCHAR column in test_cases and category performance

3. RegressionStatus
   Frontend Type: export type RegressionStatus = "PASS" | "FAIL" | "WARNING";
   Used By: Experiment, RegressionMetric, RegressionComparison, StatusBadge
   Likely Backend Entity: Enum / VARCHAR column in experiments and regression_comparisons

4. EvaluationCase
   Frontend Type: export interface EvaluationCase { id: string; input: string; expected_output: string; category: EvaluationCategory; metadata: Record<string, string>; }
   Used By: DatasetDetail, CreateDatasetPayload
   Likely Backend Entity: Table test_cases (id, dataset_id, input, expected_output, category, metadata_json)

5. Dataset & DatasetDetail
   Frontend Type: export interface Dataset { id: string; name: string; description: string; case_count: number; categories: EvaluationCategory[]; created_at: string; updated_at: string; }
   Used By: Datasets page, New Evaluation page, Experiments page
   Likely Backend Entity: Table datasets (id, name, description, created_at, updated_at)

6. ModelConfiguration
   Frontend Type: export interface ModelConfiguration { id: string; name: string; provider: Provider; model: string; temperature: number; max_tokens: number; created_at: string; }
   Used By: Configurations page, New Evaluation page
   Likely Backend Entity: Table model_configs (id, name, provider, model, temperature, max_tokens, created_at)

7. PromptVersion & PromptConfiguration
   Frontend Type: export interface PromptConfiguration { id: string; name: string; status: PromptStatus; latest_version: number; versions: PromptVersion[]; created_at: string; }
   Used By: Configurations page, New Evaluation page
   Likely Backend Entity: Tables prompts (id, name, status, created_at) and prompt_versions (id, prompt_id, version, system_prompt, user_template, notes, created_at)

8. Experiment
   Frontend Type: export interface Experiment { id: string; name: string; dataset_id: string; dataset_name: string; model_config_id: string; provider: Provider; model: string; prompt_id: string; prompt_name: string; prompt_version: number; metrics: MetricKey[]; quality_score: number; pass_rate: number; avg_latency_ms: number; p95_latency_ms: number; total_tokens: number; estimated_cost: number; regression_status: RegressionStatus; status: ExperimentStatus; created_at: string; }
   Used By: Dashboard, Experiments list, Regression comparison
   Likely Backend Entity: Table experiments (id, name, dataset_id, model_config_id, prompt_version_id, status, quality_score, pass_rate, avg_latency_ms, p95_latency_ms, total_tokens, estimated_cost, regression_status, created_at)

9. EvaluationCaseResult
   Frontend Type: export interface EvaluationCaseResult { id: string; case_id: string; input: string; expected_output: string; model_output: string; category: EvaluationCategory; score: number; latency_ms: number; tokens: number; status: CaseStatus; metric_scores: MetricResult[]; failure_reason: string | null; judge_explanation: string; }
   Used By: Experiment Details page, CaseDetailDrawer
   Likely Backend Entity: Table test_case_results (id, experiment_id, test_case_id, model_output, score, latency_ms, tokens, status, metric_scores_json, failure_reason, judge_explanation)

10. RegressionComparison & PromotionGate
   Frontend Type: export interface RegressionComparison { baseline: Experiment; candidate: Experiment; verdict: RegressionStatus; summary: string; metrics: RegressionMetric[]; categories: CategoryRegression[]; regressed_cases: RegressionCase[]; improved_cases: RegressionCase[]; promotion_gate: PromotionGate; }
   Used By: Regression comparison page (/regression)
   Likely Backend Entity: Computed result dynamically or persisted in table regression_comparisons (id, baseline_experiment_id, candidate_experiment_id, verdict, summary_json, promotion_gate_json, created_at)

11. Settings & RegressionThresholds
   Frontend Type: export interface Settings { evaluation_defaults: EvaluationDefaults; regression_thresholds: RegressionThresholds; providers: ProviderStatus[]; }
   Used By: Settings page (/settings), Regression engine
   Likely Backend Entity: Table settings (id, evaluation_defaults_json, regression_thresholds_json, updated_at)
```

---

## 7. User Action → Backend Requirement Matrix

| Frontend Page                | User Action                            | Component / Handler                     | Current Behaviour                                                                         | Required Backend Operation                                                                                           |
| :--------------------------- | :------------------------------------- | :-------------------------------------- | :---------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------- |
| `/datasets`                  | Click "New Dataset" & Submit           | `DatasetsPage` modal form               | Parses pipe-delimited text, updates in-memory array `datasetDetails`, shows toast         | `POST /api/v1/datasets` with JSON payload or file upload                                                             |
| `/datasets/$datasetId`       | Click "Add Case" & Submit              | `DatasetDetailPage` modal form          | Appends case to mock array `datasetDetails`, updates case count                           | `POST /api/v1/datasets/{dataset_id}/cases`                                                                           |
| `/datasets/$datasetId`       | Search or filter cases                 | `Input` & `Select` state                | Client-side filter on `data.cases`                                                        | `GET /api/v1/datasets/{dataset_id}?search=...&category=...`                                                          |
| `/configurations`            | Create Model Configuration             | `ConfigurationsPage` modal form         | Calls `createModelConfiguration()`, appends to in-memory `modelConfigurations`            | `POST /api/v1/configurations/models`                                                                                 |
| `/configurations`            | Create Prompt Configuration            | `ConfigurationsPage` modal form         | Calls `createPromptConfiguration()`, appends to `promptConfigurations`                    | `POST /api/v1/configurations/prompts`                                                                                |
| `/configurations`            | Add Prompt Version                     | `ConfigurationsPage` version form       | Calls `createPromptVersion()`, pushes new version object into prompt array                | `POST /api/v1/configurations/prompts/{prompt_id}/versions`                                                           |
| `/evaluations/new`           | Click "Run Evaluation"                 | `NewEvaluationPage.start()`             | Calls `runEvaluation()`, simulates 4 progress steps with `delay()`, generates mock scores | `POST /api/v1/evaluations/run` (returns `job_id`), followed by `GET /api/v1/evaluations/jobs/{job_id}` SSE / polling |
| `/experiments`               | Filter experiment table                | `ExperimentsPage` dropdowns & inputs    | Calls `listExperiments(filters)`, filters in-memory seed array                            | `GET /api/v1/experiments?search=...&dataset_id=...&provider=...&model=...&status=...`                                |
| `/experiments`               | Select 2 experiments & click "Compare" | `ExperimentsPage.compare()`             | Navigates to `/regression?baseline=A&candidate=B`                                         | Navigates to `/regression` route (reads search params)                                                               |
| `/experiments/$experimentId` | Click case row                         | `ExperimentResultsPage` row click       | Opens `CaseDetailDrawer` with selected `EvaluationCaseResult`                             | `GET /api/v1/experiments/{experiment_id}/cases/{case_id}` (or returned in experiment result detail)                  |
| `/regression`                | Change baseline / candidate dropdowns  | `RegressionPage` dropdown handlers      | Updates URL search params, triggers `compareExperiments()`                                | `POST /api/v1/regressions/compare` (or `GET /api/v1/comparisons?baseline=A&candidate=B`)                             |
| `/regression`                | Click regressed/improved case row      | `RegressionPage` table row click        | Opens side-by-side inspection dialog showing baseline vs candidate output & judge notes   | Data provided directly in `RegressionComparison.regressed_cases` payload                                             |
| `/settings`                  | Save Evaluation Defaults               | `SettingsPage.saveEvalDefaultsMutation` | Calls `updateEvaluationDefaults()`, updates in-memory `state`                             | `PUT /api/v1/settings/evaluation`                                                                                    |
| `/settings`                  | Save Regression Thresholds             | `SettingsPage.saveThresholdsMutation`   | Calls `updateRegressionThresholds()`, updates in-memory `state`                           | `PUT /api/v1/settings/regression`                                                                                    |

---

## 8. Proposed REST API Contract

### Resource 1: Dashboard (`/api/v1/dashboard`)

- `GET /api/v1/dashboard`
  - **Purpose**: Retrieve summary health metrics, quality/latency/cost trends, recent runs, and regression alerts.
  - **Frontend Consumer**: Dashboard page ([src/routes/index.tsx](file:///d:/Projects/LLM-Guard/llm-guard-main/src/routes/index.tsx)).
  - **Request**: None.
  - **Response (200 OK)**:
    ```json
    {
      "total_experiments": 14,
      "evaluations_this_week": 6,
      "avg_quality_score": 88.4,
      "avg_latency_ms": 740,
      "estimated_cost": 4.12,
      "regression_pass_rate": 78.6,
      "quality_over_time": [{ "date": "Jul 20", "score": 91.4 }],
      "latency_over_time": [{ "date": "Jul 20", "latency": 810 }],
      "cost_over_time": [{ "date": "Jul 20", "cost": 0.45 }],
      "recent_experiments": [],
      "alerts": [
        {
          "id": "alt-01",
          "severity": "FAIL",
          "message": "...",
          "experiment_id": "exp-014",
          "created_at": "..."
        }
      ]
    }
    ```

### Resource 2: Datasets (`/api/v1/datasets`)

- `GET /api/v1/datasets` — List datasets summary.
- `POST /api/v1/datasets` — Create dataset with initial test cases.
- `GET /api/v1/datasets/{dataset_id}` — Get dataset details and test cases.
- `POST /api/v1/datasets/{dataset_id}/cases` — Add test case to dataset.

### Resource 3: Configurations (`/api/v1/configurations`)

- `GET /api/v1/configurations/models` — List model configurations.
- `POST /api/v1/configurations/models` — Create model configuration.
- `GET /api/v1/configurations/prompts` — List prompt configurations with versions.
- `POST /api/v1/configurations/prompts` — Create prompt configuration.
- `POST /api/v1/configurations/prompts/{prompt_id}/versions` — Create new version for a prompt.

### Resource 4: Experiments (`/api/v1/experiments`)

- `GET /api/v1/experiments` — Query filterable list of experiments (`search`, `dataset_id`, `provider`, `model`, `status`).
- `GET /api/v1/experiments/{experiment_id}` — Get detailed experiment result, metric breakdown, category performance, and case results.

### Resource 5: Evaluations Execution (`/api/v1/evaluations`)

- `POST /api/v1/evaluations/run` — Launch evaluation execution job.
  - **Request Body**:
    ```json
    {
      "name": "Support v5 — candidate run",
      "dataset_id": "ds-support",
      "model_config_id": "mc-groq-70b",
      "prompt_id": "pc-support",
      "prompt_version": 4,
      "metrics": ["semantic_similarity", "llm_judge", "response_completeness"]
    }
    ```
  - **Response (202 Accepted)**: `{"job_id": "job-8812a", "status": "preparing"}`
- `GET /api/v1/evaluations/jobs/{job_id}` — Poll job status & progress (`preparing`, `running`, `scoring`, `complete`).

### Resource 6: Regressions & Comparisons (`/api/v1/regressions`)

- `POST /api/v1/regressions/compare` — Compare baseline experiment vs candidate experiment.
  - **Request Body**: `{"baseline_experiment_id": "exp-013", "candidate_experiment_id": "exp-014"}`
  - **Response (200 OK)**: Returns full `RegressionComparison` schema including verdict, promotion gate rules, metric deltas, category regressions, regressed cases, and improved cases.

### Resource 7: Settings (`/api/v1/settings`)

- `GET /api/v1/settings` — Get workspace settings (evaluation defaults, regression thresholds, provider statuses).
- `PUT /api/v1/settings/evaluation` — Update evaluation defaults.
- `PUT /api/v1/settings/regression` — Update regression thresholds policy.

---

## 9. Proposed PostgreSQL Schema

```sql
-- 1. Datasets Table
CREATE TABLE datasets (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Test Cases Table
CREATE TABLE test_cases (
    id VARCHAR(64) PRIMARY KEY,
    dataset_id VARCHAR(64) NOT NULL REFERENCES datasets(id) ON DELETE CASCADE,
    input TEXT NOT NULL,
    expected_output TEXT NOT NULL,
    category VARCHAR(64) NOT NULL,
    metadata_json JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_test_cases_dataset ON test_cases(dataset_id);
CREATE INDEX idx_test_cases_category ON test_cases(category);

-- 3. Model Configurations Table
CREATE TABLE model_configs (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    provider VARCHAR(32) NOT NULL, -- 'groq', 'gemini'
    model VARCHAR(128) NOT NULL,
    temperature NUMERIC(3,2) NOT NULL DEFAULT 0.2,
    max_tokens INTEGER NOT NULL DEFAULT 1024,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Prompts Table
CREATE TABLE prompts (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'draft', -- 'active', 'draft', 'archived'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Prompt Versions Table
CREATE TABLE prompt_versions (
    id VARCHAR(64) PRIMARY KEY,
    prompt_id VARCHAR(64) NOT NULL REFERENCES prompts(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    system_prompt TEXT NOT NULL,
    user_template TEXT NOT NULL,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_prompt_version UNIQUE (prompt_id, version)
);

-- 6. Experiments Table
CREATE TABLE experiments (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    dataset_id VARCHAR(64) NOT NULL REFERENCES datasets(id),
    model_config_id VARCHAR(64) NOT NULL REFERENCES model_configs(id),
    prompt_version_id VARCHAR(64) NOT NULL REFERENCES prompt_versions(id),
    status VARCHAR(32) NOT NULL DEFAULT 'running', -- 'running', 'completed', 'failed'
    quality_score NUMERIC(5,2),
    pass_rate NUMERIC(5,2),
    avg_latency_ms INTEGER,
    p95_latency_ms INTEGER,
    total_tokens INTEGER,
    estimated_cost NUMERIC(10,4),
    regression_status VARCHAR(32), -- 'PASS', 'WARNING', 'FAIL'
    metrics_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_experiments_dataset ON experiments(dataset_id);
CREATE INDEX idx_experiments_created ON experiments(created_at DESC);

-- 7. Test Case Results Table (Raw Telemetry & Evaluation Scores)
CREATE TABLE test_case_results (
    id VARCHAR(64) PRIMARY KEY,
    experiment_id VARCHAR(64) NOT NULL REFERENCES experiments(id) ON DELETE CASCADE,
    test_case_id VARCHAR(64) NOT NULL REFERENCES test_cases(id),
    model_output TEXT NOT NULL,
    score NUMERIC(5,2) NOT NULL,
    latency_ms INTEGER NOT NULL,
    tokens INTEGER NOT NULL,
    status VARCHAR(16) NOT NULL, -- 'PASS', 'FAIL'
    metric_scores_json JSONB NOT NULL,
    failure_reason TEXT,
    judge_explanation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_case_results_experiment ON test_case_results(experiment_id);

-- 8. Workspace Settings Table
CREATE TABLE workspace_settings (
    id VARCHAR(64) PRIMARY KEY DEFAULT 'default',
    evaluation_defaults_json JSONB NOT NULL,
    regression_thresholds_json JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 10. Model Provider Abstraction

The backend will route all LLM requests through a unified `ModelGateway` abstraction.

### Provider Gateway Interface

```python
class LLMResponse(BaseModel):
    text: str
    provider: str  # "groq" | "gemini"
    model: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    total_tokens: int
    estimated_cost: float
    finish_reason: str
    error: Optional[str] = None
    retry_count: int = 0

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str, temperature: float, max_tokens: int) -> LLMResponse:
        pass
```

---

## 11. Evaluation Engine Specification

The evaluation engine computes scores per test case across 3 evaluator types:

1. **Deterministic Evaluators**:
   - `exact_match`: Normalized string equality ($100.0$ or $0.0$).
   - `keyword_match`: Ratio of key terms present in output.
2. **Semantic Evaluators**:
   - `semantic_similarity`: Embedding vector cosine similarity or token overlap ratio.
3. **LLM-as-a-Judge Evaluators**:
   - `llm_judge` & `response_completeness`: Structured prompt sent to a high-capacity judge model (e.g. `llama-3.3-70b-versatile` or `gemini-3.6-flash`) returning JSON: `{"score": 85, "reasoning": "...", "passed": true}`.

---

## 12. Experiment Runner Design

### Execution Pipeline

```text
Request POST /api/v1/evaluations/run
  ↓
1. Load dataset cases & render prompt templates ({{input}})
  ↓
2. Dispatch async batch requests via ModelGateway (bounded by concurrency setting, e.g. 5)
  ↓
3. Collect raw LLM responses & latency/token telemetry
  ↓
4. Pass (input, expected, output) to selected Evaluator suite
  ↓
5. Persist per-case results to test_case_results
  ↓
6. Aggregate overall quality_score, pass_rate, avg_latency_ms, p95_latency_ms, total_tokens, estimated_cost
  ↓
7. Mark experiment status as 'completed'
```

---

## 13. Regression Engine Specification

The regression engine compares a **Baseline Experiment** against a **Candidate Experiment** using configured `RegressionThresholds`.

### Promotion Gate Evaluation Logic

1. **Overall Quality Regression**: `candidate.quality_score - baseline.quality_score >= -max_quality_regression_pct`
2. **Factuality Regression**: `candidate.factuality - baseline.factuality >= -max_factuality_regression_pct`
3. **Latency Increase**: `((candidate.latency - baseline.latency) / baseline.latency) * 100 <= max_latency_increase_pct`
4. **Cost Increase**: `((candidate.cost - baseline.cost) / baseline.cost) * 100 <= max_cost_increase_pct`
5. **Critical Category Regression**: Zero tolerance for score drops (`delta < 0%`) on categories marked critical.
6. **Newly Failing Cases**: Count of cases that passed in baseline but failed in candidate must equal 0.

If any rule fails, `verdict = "FAIL"` and `promotion_gate.passed = false`, generating explicit human-readable failure explanations.

---

## 14. Dashboard Aggregation Requirements

| Dashboard Component      | Required Aggregation Query                                                                    | Source Table(s) |
| :----------------------- | :-------------------------------------------------------------------------------------------- | :-------------- |
| Total Experiments        | `COUNT(id)`                                                                                   | `experiments`   |
| Evaluations This Week    | `COUNT(id) WHERE created_at >= NOW() - INTERVAL '7 days'`                                     | `experiments`   |
| Avg Quality Score        | `AVG(quality_score)`                                                                          | `experiments`   |
| Avg Latency              | `AVG(avg_latency_ms)`                                                                         | `experiments`   |
| Estimated Cost           | `SUM(estimated_cost)`                                                                         | `experiments`   |
| Regression Pass Rate     | `(COUNT(WHERE regression_status = 'PASS') / COUNT(*)) * 100`                                  | `experiments`   |
| Quality Over Time Chart  | `SELECT DATE(created_at), AVG(quality_score) GROUP BY DATE(created_at)`                       | `experiments`   |
| Latency / Cost Over Time | `SELECT DATE(created_at), AVG(avg_latency_ms), SUM(estimated_cost) GROUP BY DATE(created_at)` | `experiments`   |
| Recent Experiments       | `SELECT * ORDER BY created_at DESC LIMIT 5`                                                   | `experiments`   |

---

## 15. Frontend/Backend Gap Analysis

### Current Status Matrix

- **Already Ready**: Frontend pages, routes, TanStack Query hooks, navigation, modals, side-by-side inspection drawers, design system, theme switching.
- **Mocked**: `src/api/*.ts` currently calls `src/mocks/data.ts` using client-side `delay()`.
- **Incomplete**: Real-time evaluation progress streaming (currently uses client `setTimeout` loop in `evaluations.ts`).
- **Missing**: Real FastAPI backend, PostgreSQL database, real Groq/Gemini API calls, real evaluator execution.
- **Inconsistent**: None identified; service layer interfaces align cleanly with required FastAPI schemas.

---

## 16. Recommended Backend Directory Structure

```text
backend/
├── app/
│   ├── api/
│   │   ├── v1/
│   │   │   ├── router.py
│   │   │   ├── dashboard.py
│   │   │   ├── datasets.py
│   │   │   ├── configurations.py
│   │   │   ├── evaluations.py
│   │   │   ├── experiments.py
│   │   │   ├── regressions.py
│   │   │   └── settings.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   ├── models/                  # SQLAlchemy DB Models
│   │   ├── dataset.py
│   │   ├── experiment.py
│   │   ├── prompt.py
│   │   └── settings.py
│   ├── schemas/                 # Pydantic Schemas
│   │   ├── dataset.py
│   │   ├── experiment.py
│   │   ├── regression.py
│   │   └── settings.py
│   ├── services/
│   │   ├── evaluators/          # Exact match, semantic, LLM judge
│   │   ├── providers/           # Groq & Gemini gateways
│   │   ├── experiment_runner.py
│   │   └── regression_engine.py
│   └── main.py                  # FastAPI Application Entry
├── tests/                       # Pytest test suite
├── alembic/                     # Database migrations
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## 17. Backend Implementation Phases

```text
Phase 1: Backend Foundation (FastAPI, Pydantic, CORS, Database Connection)
Phase 2: Database Schema & Datasets Management API
Phase 3: Model & Prompt Configuration API
Phase 4: LLM Provider Gateway (Groq & Gemini integration)
Phase 5: Evaluation Engine (Deterministic, Semantic, LLM Judge evaluators)
Phase 6: Async Experiment Runner & Telemetry Collection
Phase 7: Regression Engine & Promotion Gate Policy Evaluator
Phase 8: Frontend Integration (Replace mock API calls with FastAPI fetch calls)
Phase 9: Testing, Docker Compose, & Production Polish
```

---

## 18. MVP Acceptance Criteria

1. User can create an evaluation dataset with test cases.
2. User can configure Groq/Gemini models and versioned system prompts.
3. User can launch an evaluation run against configured LLMs.
4. Backend collects response text, latency ms, token counts, and calculates scores.
5. User can select baseline and candidate experiments on `/regression`.
6. Backend computes metric deltas, category regressions, regressed cases, and evaluates Promotion Gate rules.
7. Candidate promotion is flagged as `PASSED` or `BLOCKED` with explainable failure reasons.
8. All 9 frontend routes function seamlessly with real PostgreSQL persistence.

---

## 19. Risks / Open Technical Decisions

1. **LLM Provider Rate Limits**: High concurrency on large datasets may hit Groq/Gemini RPM/TPM limits. _Mitigation: Implement semaphore concurrency limits and exponential backoff retries in `ModelGateway`._
2. **LLM Judge Cost & Latency**: Running an LLM judge on every case increases eval cost. _Mitigation: Allow user to select metric subsets (e.g. deterministic + semantic only for fast passes)._

---

## 20. Final Audit Summary

The repository audit confirms that the React + TypeScript frontend is architecturally sound, fully styled, and cleanly modularized. Its centralized API client layer (`src/api/*`) and domain types (`src/types/index.ts`) provide an exact, drop-in interface for the proposed FastAPI backend.
