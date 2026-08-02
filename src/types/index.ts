export type Provider = "groq" | "gemini";

export type EvaluationCategory =
  | "factuality"
  | "reasoning"
  | "summarization"
  | "customer-support"
  | "instruction-following"
  | "safety"
  | "billing"
  | "technical"
  | "account-management"
  | "general";

export type RegressionStatus = "PASS" | "FAIL" | "WARNING";
export type CaseStatus = "PASS" | "FAIL";
export type ExperimentStatus = "completed" | "running" | "failed";
export type PromptStatus = "active" | "draft" | "archived";

export type MetricKey =
  "exact_match" | "keyword_match" | "semantic_similarity" | "llm_judge" | "response_completeness";

export interface EvaluationCase {
  id: string;
  input: string;
  expected_output: string;
  category: EvaluationCategory;
  metadata: Record<string, string>;
}

export interface Dataset {
  id: string;
  name: string;
  description: string;
  case_count: number;
  categories: EvaluationCategory[];
  created_at: string;
  updated_at: string;
}

export interface DatasetDetail extends Dataset {
  cases: EvaluationCase[];
}

export interface CreateDatasetPayload {
  name: string;
  description: string;
  cases: Omit<EvaluationCase, "id">[];
}

export interface ModelConfiguration {
  id: string;
  name: string;
  provider: Provider;
  model: string;
  temperature: number;
  max_tokens: number;
  created_at: string;
}

export type CreateModelConfigurationPayload = Omit<ModelConfiguration, "id" | "created_at">;

export interface PromptVersion {
  id: string;
  version: number;
  system_prompt: string;
  user_template: string;
  notes: string;
  created_at: string;
}

export interface PromptConfiguration {
  id: string;
  name: string;
  status: PromptStatus;
  latest_version: number;
  versions: PromptVersion[];
  created_at: string;
}

export interface MetricResult {
  key: MetricKey | string;
  label: string;
  score: number;
}

export interface Experiment {
  id: string;
  name: string;
  dataset_id: string;
  dataset_name: string;
  model_config_id: string;
  provider: Provider;
  model: string;
  prompt_id: string;
  prompt_name: string;
  prompt_version: number;
  metrics: MetricKey[];
  quality_score: number;
  pass_rate: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  total_tokens: number;
  estimated_cost: number;
  regression_status: RegressionStatus;
  status: ExperimentStatus;
  created_at: string;
}

export interface EvaluationCaseResult {
  id: string;
  case_id: string;
  input: string;
  expected_output: string;
  model_output: string;
  category: EvaluationCategory;
  score: number;
  latency_ms: number;
  tokens: number;
  status: CaseStatus;
  metric_scores: MetricResult[];
  failure_reason: string | null;
  judge_explanation: string;
}

export interface ExperimentResult {
  experiment: Experiment;
  metric_breakdown: MetricResult[];
  category_performance: MetricResult[];
  quality_trend: { date: string; score: number }[];
  cases: EvaluationCaseResult[];
}

export interface RegressionMetric {
  key: string;
  label: string;
  baseline: number;
  candidate: number;
  delta_pct: number;
  threshold_pct: number;
  direction: "higher_is_better" | "lower_is_better";
  unit: "percent" | "ms" | "usd";
  status: RegressionStatus;
}

export interface CategoryRegression {
  category: EvaluationCategory;
  baseline: number;
  candidate: number;
  delta_pct: number;
  critical: boolean;
}

export interface RegressionCase {
  case_id: string;
  input: string;
  expected_output: string;
  category: EvaluationCategory;
  baseline_score: number;
  candidate_score: number;
  delta: number;
  baseline_output: string;
  candidate_output: string;
  failure_reason: string;
  judge_explanation: string;
}

export interface PromotionGateRule {
  label: string;
  limit: string;
  actual: string;
  passed: boolean;
}

export interface PromotionGate {
  passed: boolean;
  rules: PromotionGateRule[];
  reasons: string[];
}

export interface RegressionComparison {
  baseline: Experiment;
  candidate: Experiment;
  verdict: RegressionStatus;
  summary: string;
  metrics: RegressionMetric[];
  categories: CategoryRegression[];
  regressed_cases: RegressionCase[];
  improved_cases: RegressionCase[];
  promotion_gate: PromotionGate;
}

export interface RegressionThresholds {
  max_quality_regression_pct: number;
  max_factuality_regression_pct: number;
  max_latency_increase_pct: number;
  max_cost_increase_pct: number;
  critical_categories: EvaluationCategory[];
}

export interface EvaluationDefaults {
  default_metrics: MetricKey[];
  concurrency: number;
  judge_model: string;
}

export interface ProviderStatus {
  provider: Provider;
  label: string;
  configured: boolean;
  models: string[];
}

export interface Settings {
  evaluation_defaults: EvaluationDefaults;
  regression_thresholds: RegressionThresholds;
  providers: ProviderStatus[];
}

export interface CreateEvaluationPayload {
  name: string;
  dataset_id: string;
  model_config_id: string;
  prompt_id: string;
  prompt_version: number;
  metrics: MetricKey[];
}

export interface EvaluationProgress {
  stage: "preparing" | "running" | "scoring" | "complete";
  message: string;
  completed: number;
  total: number;
}

export interface DashboardSummary {
  total_experiments: number;
  evaluations_this_week: number;
  avg_quality_score: number;
  avg_latency_ms: number;
  estimated_cost: number;
  regression_pass_rate: number;
  quality_over_time: { date: string; score: number }[];
  latency_over_time: { date: string; latency: number }[];
  cost_over_time: { date: string; cost: number }[];
  recent_experiments: Experiment[];
  alerts: {
    id: string;
    severity: RegressionStatus;
    message: string;
    experiment_id: string;
    created_at: string;
  }[];
}

export interface ExperimentFilters {
  search?: string;
  dataset_id?: string;
  provider?: Provider | "all";
  model?: string;
  prompt_version?: string;
  status?: RegressionStatus | "all";
  since?: string;
}
