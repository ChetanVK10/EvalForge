# LLM Guard

You are a Senior Product Designer and Senior Frontend Engineer.

Build the frontend for a portfolio-quality AI engineering platform called:

# LLMOps Studio

## Product Goal

LLMOps Studio is an LLM Evaluation, Regression Testing, and Observability Platform.

It helps AI engineers:

- create evaluation datasets

- configure LLM providers and prompts

- run repeatable LLM evaluations

- compare experiment runs

- track quality, latency, token usage, and estimated cost

- detect regressions between prompt/model versions

- inspect failures by category

- decide whether a new configuration should PASS or FAIL a promotion gate

IMPORTANT:

This project is NOT an LLM fine-tuning platform.

Do NOT build:

- model training

- QLoRA

- PEFT

- GPU management

- CUDA functionality

- Hugging Face training pipelines

The focus is:

LLM Evaluation + Regression Testing + Observability.

==========================================================

TECH STACK

==========================================================

Frontend:

- React

- TypeScript

- Vite

- Tailwind CSS

- shadcn/ui

- Recharts or another lightweight React charting library

- Lucide icons

The production backend will be built separately using:

- Python

- FastAPI

- PostgreSQL

- SQLAlchemy

- Pydantic

LLM providers will eventually include:

- Groq

- Google Gemini

IMPORTANT:

Do NOT implement the production backend.

For now:

- use realistic mock data

- create clean TypeScript interfaces

- create a centralized API/service layer

- keep frontend components independent from mock-data implementation

- structure the application so mock services can later be replaced by FastAPI endpoints without rewriting UI components

==========================================================

DESIGN DIRECTION

==========================================================

The application should look like a professional internal AI engineering platform.

Think:

- experiment tracking dashboard

- developer tooling

- ML/LLM observability

- modern SaaS admin interface

Avoid:

- flashy AI gradients everywhere

- excessive animations

- giant marketing-style cards

- chatbot-style UI

- excessive rounded containers

- unnecessary visual clutter

Prefer:

- clean spacing

- dense but readable information

- professional typography

- clear metric hierarchy

- tables

- charts

- status indicators

- filters

- tabs

- comparison views

Use a desktop-first responsive layout.

Support both:

- Light mode

- Dark mode

==========================================================

APPLICATION LAYOUT

==========================================================

Create a persistent sidebar.

Sidebar navigation:

1. Dashboard

2. Datasets

3. Configurations

4. Evaluations

5. Experiments

6. Regression

7. Settings

Top bar should contain:

- current page title

- optional breadcrumb

- search where appropriate

- theme toggle

- compact user/profile area

==========================================================

PAGE 1 — DASHBOARD

==========================================================

Purpose:

Give engineers an immediate overview of evaluation health.

Top metric cards:

- Total Experiments

- Evaluations This Week

- Average Quality Score

- Average Latency

- Estimated Cost

- Regression Pass Rate

Include charts:

1. Quality Score Over Time

2. Average Latency Over Time

3. Estimated Cost Over Time

Include:

Recent Experiments table.

Columns:

Experiment

Model

Dataset

Prompt Version

Quality Score

Latency

Cost

Regression Status

Created At

Regression statuses:

PASS

FAIL

WARNING

Use appropriate badges.

Also include:

Recent Regression Alerts

Example:

"Prompt v4 decreased factuality by 8.2% compared with v3."

==========================================================

PAGE 2 — DATASETS

==========================================================

Purpose:

Manage evaluation datasets.

Main table:

Dataset Name

Description

Number of Cases

Categories

Created At

Last Updated

Actions

Primary action:

"+ New Dataset"

Dataset creation should support:

- dataset name

- description

- evaluation cases

Each evaluation case should conceptually contain:

id

input

expected_output

category

metadata

Categories might include:

- factuality

- reasoning

- summarization

- customer-support

- instruction-following

- safety

Create a Dataset Details page.

Show:

Dataset information

Number of examples

Category distribution

Evaluation cases table

Case table:

Input

Expected Output

Category

Metadata

Actions

Support mock actions:

Add Case

Edit Case

Delete Case

Import JSONL

The Import JSONL button only needs frontend behavior for now.

==========================================================

PAGE 3 — CONFIGURATIONS

==========================================================

Purpose:

Manage model and prompt configurations used during evaluations.

Create tabs:

Model Configurations

Prompt Configurations

---

MODEL CONFIGURATIONS

---

Show cards/table containing:

Configuration Name

Provider

Model

Temperature

Max Tokens

Created At

Supported mock providers:

Groq

Gemini

Example models can include realistic provider model names, but keep model selection configurable rather than hardcoding application logic around specific models.

Create Model Configuration form:

Configuration Name

Provider

Model

Temperature

Max Tokens

Do NOT request API keys here.

API keys will eventually be handled securely by the backend/environment configuration.

---

PROMPT CONFIGURATIONS

---

Show:

Prompt Name

Version

System Prompt Preview

Created At

Status

Statuses:

Active

Draft

Archived

Allow:

Create Prompt

Edit Prompt

Create New Version

View Version History

Example:

Customer Support Assistant

v1

v2

v3

v4

Prompt versioning is extremely important because regression testing will compare different prompt versions.

==========================================================

PAGE 4 — NEW EVALUATION

==========================================================

Purpose:

Configure and launch an evaluation experiment.

Create a step-based or clean single-page form.

Fields:

Experiment Name

Dataset

Model Configuration

Prompt Configuration

Prompt Version

Evaluation Metrics

Allow selecting metrics such as:

- Exact Match

- Keyword Match

- Semantic Similarity

- LLM Judge

- Response Completeness

Show an Evaluation Summary before running:

Dataset

Number of cases

Provider

Model

Prompt version

Selected metrics

Primary button:

"Run Evaluation"

Since backend does not exist yet:

simulate execution.

Show progress such as:

Preparing evaluation...

Running 25 / 100 cases

Calculating metrics...

Evaluation complete

Then navigate to the Experiment Results page.

Keep this execution mechanism isolated inside the mock service layer so it can later be replaced by a FastAPI request.

==========================================================

PAGE 5 — EXPERIMENT RESULTS

==========================================================

This is one of the most important pages.

Header:

Experiment Name

Experiment ID

Created At

Dataset

Model

Prompt Version

Status

Top metrics:

Overall Quality Score

Pass Rate

Average Latency

P95 Latency

Total Tokens

Estimated Cost

Include charts:

Metric Breakdown

Example:

Factuality 92%

Reasoning 87%

Completeness 94%

Instruction 89%

Category Performance

Example:

Customer Support 93%

Billing 88%

Technical 84%

General 95%

Include an Evaluation Cases table.

Columns:

Input

Expected Output

Model Output

Score

Latency

Tokens

Status

Statuses:

PASS

FAIL

Clicking a row should open a detailed case drawer/modal.

Show:

Input

Expected Output

Actual Model Output

Metric Scores

Latency

Token Usage

Failure Reason

LLM Judge Explanation

This failure inspection experience is important.

==========================================================

PAGE 6 — REGRESSION COMPARISON

==========================================================

THIS IS THE CENTERPIECE OF THE PROJECT.

Design this page particularly well.

Purpose:

Compare a baseline experiment against a candidate experiment.

Top selectors:

Baseline Experiment

vs

Candidate Experiment

Example:

Prompt v3

vs

Prompt v4

Display a prominent overall verdict:

PASS

or

FAIL

Example:

REGRESSION CHECK: FAIL

Candidate quality decreased beyond the configured threshold.

---

COMPARISON METRICS

---

Create a comparison table:

Metric

Baseline

Candidate

Difference

Threshold

Status

Example:

Overall Quality

91.2%

88.5%

-2.7%

-2.0%

FAIL

Factuality

93.1%

84.9%

-8.2%

-3.0%

FAIL

Completeness

89.5%

92.1%

+2.6%

-3.0%

PASS

Latency

820 ms

760 ms

-7.3%

+15%

PASS

Cost

$0.42

$0.39

-7.1%

+10%

PASS

Use:

green = improvement/pass

red = regression/fail

neutral styling for insignificant changes

---

CATEGORY REGRESSION

---

Show category-level comparison.

Example:

Billing

Technical Support

Account Management

General Questions

Show baseline score, candidate score and delta.

---

REGRESSED CASES

---

Create a section:

"Regressed Cases"

These are evaluation cases that passed in baseline but failed in candidate.

Columns:

Input

Category

Baseline Score

Candidate Score

Delta

Failure Reason

Clicking a case should show side-by-side comparison:

INPUT

EXPECTED OUTPUT

BASELINE OUTPUT

CANDIDATE OUTPUT

BASELINE SCORE

CANDIDATE SCORE

LLM JUDGE EXPLANATION

This should be one of the strongest visual parts of the application.

---

IMPROVED CASES

---

Also show:

"Improved Cases"

Cases where candidate significantly outperformed baseline.

==========================================================

PROMOTION GATE

==========================================================

The Regression page should contain a Promotion Gate section.

Example policy:

Overall quality decrease <= 2%

Factuality decrease <= 3%

Latency increase <= 15%

Cost increase <= 10%

Critical-category regression = 0

Show:

Promotion Gate

PASS / FAIL

If failed, clearly explain why.

Example:

Promotion blocked.

Reasons:

Factuality decreased 8.2%, exceeding allowed regression of 3%.

3 previously passing evaluation cases now fail.

Do not use fake AI reasoning here.

These explanations should be deterministic based on mock metric differences.

==========================================================

PAGE 7 — EXPERIMENTS

==========================================================

Create a searchable/filterable experiment history table.

Columns:

Experiment

Dataset

Provider

Model

Prompt

Version

Quality

Latency

Cost

Status

Created

Filters:

Dataset

Provider

Model

Prompt Version

Status

Date

Click experiment -> Experiment Results.

Allow selecting two experiments and clicking:

"Compare"

which navigates to Regression Comparison.

==========================================================

PAGE 8 — SETTINGS

==========================================================

Keep this simple.

Sections:

Evaluation Defaults

Regression Thresholds

Example regression settings:

Maximum Quality Regression

Maximum Factuality Regression

Maximum Latency Increase

Maximum Cost Increase

Provider Status

Groq

Gemini

Show provider state as:

Configured

Not Configured

Do NOT expose or store real API keys in frontend code.

==========================================================

DATA MODELS

==========================================================

Create proper TypeScript interfaces/types.

At minimum:

Dataset

EvaluationCase

ModelConfiguration

PromptConfiguration

PromptVersion

Experiment

ExperimentResult

EvaluationCaseResult

MetricResult

RegressionComparison

RegressionMetric

RegressionCase

PromotionGate

Provider

Do NOT use `any` unless absolutely unavoidable.

==========================================================

API ARCHITECTURE

==========================================================

This is extremely important.

Create a centralized API layer.

Example structure:

src/

api/

    client.ts

    datasets.ts

    configurations.ts

    experiments.ts

    evaluations.ts

    regressions.ts

or another clean equivalent.

UI components should NOT import mock JSON directly.

Instead:

Component

    ↓

Service/API function

    ↓

Mock implementation

Later:

Component

    ↓

Same service/API function

    ↓

FastAPI backend

Design the service signatures with future REST endpoints in mind.

Expected future API concepts:

GET /api/v1/datasets

POST /api/v1/datasets

GET /api/v1/datasets/{id}

GET /api/v1/configurations/models

POST /api/v1/configurations/models

GET /api/v1/prompts

POST /api/v1/prompts

POST /api/v1/evaluations

GET /api/v1/experiments

GET /api/v1/experiments/{id}

POST /api/v1/regressions/compare

GET /api/v1/settings/regression

Do NOT build these backend endpoints.

Only make the frontend architecture compatible with them.

==========================================================

MOCK DATA

==========================================================

Populate the application with realistic mock data so every page looks functional immediately.

Create approximately:

3 datasets

3 model configurations

3 prompt configurations with multiple versions

8-12 experiments

50+ mock evaluation case results if useful

multiple regression comparisons

Make the data internally consistent.

For example:

If Dashboard shows:

Prompt v4 regression FAIL

then the corresponding regression page should also show that experiment as failed.

Do not generate random values on every render.

Mock data should be deterministic.

==========================================================

LOADING / ERROR / EMPTY STATES

==========================================================

Every major page should support:

Loading

Error

Empty

Success

Do not assume every API call succeeds.

Create reusable:

LoadingState

ErrorState

EmptyState

components where appropriate.

==========================================================

REUSABLE COMPONENTS

==========================================================

Prefer reusable components such as:

MetricCard

StatusBadge

ExperimentTable

MetricComparisonTable

RegressionBadge

PageHeader

EmptyState

ErrorState

LoadingState

CaseDetailDrawer

ProviderBadge

Do not over-componentize tiny UI fragments.

==========================================================

PROJECT STRUCTURE

==========================================================

Use a clean scalable frontend structure.

Something similar to:

src/

api/

components/

pages/

features/

hooks/

types/

mocks/

utils/

lib/

Do not create unnecessary enterprise abstractions.

Keep the architecture understandable for a small engineering team.

==========================================================

IMPORTANT ENGINEERING RULES

==========================================================

1. TypeScript strictness should be maintained.

2. Avoid `any`.

3. Avoid duplicated mock data.

4. Avoid hardcoded business logic inside React components.

5. Keep API calls in the API/service layer.

6. Keep regression calculations outside presentational components.

7. Components should primarily render state.

8. Do not create a backend.

9. Do not add authentication yet.

10. Do not add payment/billing functionality.

11. Do not add unnecessary AI features.

12. Do not add model fine-tuning.

13. Do not add WebSockets yet.

14. Do not introduce Redux unless genuinely necessary.

15. Prefer simple React state/hooks for this version.

16. Do not overengineer the project.

==========================================================

UX PRIORITY

==========================================================

Spend the most design attention on:

1. Regression Comparison

2. Experiment Results

3. Dashboard

4. New Evaluation

5. Experiments

6. Datasets

7. Configurations

8. Settings

The Regression Comparison page should be the signature feature of the product.

A recruiter opening this application should understand within 30 seconds:

"This system evaluates LLM changes and prevents bad prompts/models from being promoted."

==========================================================

DEMO STORY

==========================================================

Design the mock data around this demo scenario:

An AI engineer has:

Customer Support Evaluation Dataset

Baseline:

Groq Model

Customer Support Prompt v3

Candidate:

Same model

Customer Support Prompt v4

Prompt v4 was intended to improve response completeness.

Results:

Completeness improves.

Latency improves slightly.

Cost improves slightly.

BUT:

Factuality drops significantly.

Several billing-related cases regress.

Therefore:

REGRESSION CHECK = FAIL

PROMOTION GATE = BLOCKED

This scenario should be visible consistently across:

Dashboard

Experiments

Experiment Results

Regression Comparison

This will be the primary portfolio demo.

==========================================================

FINAL DELIVERABLE

==========================================================

Generate the complete working frontend.

Before finishing:

1. Verify navigation between all pages.

2. Verify mock data consistency.

3. Verify responsive behavior.

4. Verify light/dark themes.

5. Verify TypeScript types.

6. Verify there are no broken imports.

7. Verify charts render correctly.

8. Verify tables render correctly.

9. Verify regression comparison works with mock experiments.

10. Verify the project can later integrate with FastAPI without major frontend restructuring.

Do not build the production backend.

Do not expand the scope beyond the features described above.

Prioritize a polished, functional frontend that can immediately be exported to GitHub and then integrated with our separately developed FastAPI backend.

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/54af0465-77b1-47ae-b190-7e4302f4b9b3).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
