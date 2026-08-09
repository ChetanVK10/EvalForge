import { apiFetch } from "./client";
import type {
  DashboardSummary,
  EvaluationCaseResult,
  Experiment,
  ExperimentFilters,
  ExperimentResult,
  MetricResult,
} from "@/types";

const categoryLabels: Record<string, string> = {
  billing: "Billing",
  technical: "Technical Support",
  "account-management": "Account Management",
  general: "General Questions",
  factuality: "Factuality",
  reasoning: "Reasoning",
  summarization: "Summarization",
  "instruction-following": "Instruction Following",
  safety: "Safety",
  "customer-support": "Customer Support",
};

/** GET /api/v1/experiments */
export async function listExperiments(filters: ExperimentFilters = {}): Promise<Experiment[]> {
  const queryParams = new URLSearchParams();
  if (filters.search) queryParams.set("search", filters.search);
  if (filters.dataset_id && filters.dataset_id !== "all")
    queryParams.set("dataset_id", filters.dataset_id);
  if (filters.provider && filters.provider !== "all") queryParams.set("provider", filters.provider);
  if (filters.model && filters.model !== "all") queryParams.set("model", filters.model);
  if (filters.prompt_version && filters.prompt_version !== "all")
    queryParams.set("prompt_version", String(filters.prompt_version));
  if (filters.status && filters.status !== "all") queryParams.set("status", filters.status);
  if (filters.since) queryParams.set("since", filters.since);
  if (filters.date) queryParams.set("date", filters.date);

  const queryString = queryParams.toString();
  const path = `/experiments${queryString ? `?${queryString}` : ""}`;
  return apiFetch<Experiment[]>(path);
}

/** GET /api/v1/experiments/{id} */
export function getExperiment(id: string): Promise<Experiment> {
  return apiFetch<Experiment>(`/experiments/${id}`);
}

/** DELETE /api/v1/experiments/{id} */
export function deleteExperiment(id: string): Promise<{ id: string }> {
  return apiFetch<{ id: string }>(`/experiments/${id}`, {
    method: "DELETE",
  });
}

/** GET /api/v1/experiments/{id} (detailed result view) */
export async function getExperimentResult(id: string): Promise<ExperimentResult> {
  const detail = await apiFetch<any>(`/experiments/${id}`);

  // Build category performance list
  const category_performance: MetricResult[] = (detail.category_breakdown || []).map(
    (cat: any) => ({
      key: cat.category,
      label: categoryLabels[cat.category] ?? cat.category,
      score: cat.score,
    }),
  );

  // Build metric breakdown across all case scores
  const metricScoresMap: Record<string, number[]> = {};
  const rawCases: any[] = detail.case_results || [];

  rawCases.forEach((c) => {
    (c.scores || []).forEach((s: any) => {
      if (s.status === "success") {
        const arr = (metricScoresMap[s.metric] = metricScoresMap[s.metric] || []);
        arr.push(s.score);
      }
    });
  });

  const metric_breakdown: MetricResult[] = Object.entries(metricScoresMap).map(([key, scores]) => ({
    key,
    label: key.replace(/_/g, " ").replace(/\b\w/g, (l) => l.toUpperCase()),
    score: Number((scores.reduce((a, b) => a + b, 0) / (scores.length || 1)).toFixed(1)),
  }));

  // Build quality trend buckets
  const bucketSize = Math.max(1, Math.ceil(rawCases.length / 8));
  const quality_trend = Array.from({ length: Math.ceil(rawCases.length / bucketSize) }, (_, i) => {
    const bucket = rawCases.slice(i * bucketSize, (i + 1) * bucketSize);
    const avg =
      bucket.reduce((sum, c) => sum + (c.case_quality_score || 0), 0) / (bucket.length || 1);
    return { date: `Batch ${i + 1}`, score: Number(avg.toFixed(1)) };
  });

  // Map case results
  const CASE_PASS_THRESHOLD = 80.0;
  const cases: EvaluationCaseResult[] = rawCases.map((c) => {
    const caseScore =
      c.case_quality_score !== null && c.case_quality_score !== undefined
        ? c.case_quality_score
        : null;
    const executionStatus = c.status === "failed" ? "failed" : "completed";
    const isPassed =
      executionStatus === "completed" && caseScore !== null && caseScore >= CASE_PASS_THRESHOLD;
    let judgeExplanation = "";
    const metricDiagnostics: string[] = [];
    (c.scores || []).forEach((s: any) => {
      const metricKey = (s.metric || "").toLowerCase();
      if (metricKey === "llm_judge") {
        if (s.reasoning && !judgeExplanation) {
          judgeExplanation = s.reasoning;
        }
      } else if (s.reasoning) {
        const label = metricKey.replace(/_/g, " ").replace(/\b\w/g, (l: string) => l.toUpperCase());
        metricDiagnostics.push(`${label}: ${s.reasoning}`);
      }
    });

    return {
      id: c.id,
      case_id: c.test_case_id || c.id,
      input: c.input,
      expected_output: c.expected_output,
      model_output: c.model_output || "",
      category: c.category || "general",
      score: caseScore,
      latency_ms: c.latency_ms || 0,
      tokens: c.total_tokens || 0,
      execution_status: executionStatus,
      status: isPassed ? "PASS" : "FAIL",
      metric_scores: (c.scores || []).map((s: any) => ({
        key: s.metric,
        label: s.metric.replace(/_/g, " "),
        score: s.score,
      })),
      failure_reason:
        c.error ||
        (isPassed
          ? null
          : executionStatus === "failed"
            ? "LLM execution error"
            : `Score (${(caseScore ?? 0).toFixed(1)}%) fell below ${CASE_PASS_THRESHOLD.toFixed(1)}% quality pass threshold`),
      judge_explanation: judgeExplanation,
      metric_diagnostics: metricDiagnostics,
    };
  });

  const experiment: Experiment = {
    id: detail.id,
    name: detail.name,
    dataset_id: detail.dataset_id,
    dataset_name: detail.dataset_name,
    model_config_id: detail.model_config_id,
    model_config_name:
      detail.model_config_name || detail.snapshots?.model_config_name || "Model Config",
    provider: detail.provider,
    model: detail.model,
    prompt_id: detail.prompt_id,
    prompt_name: detail.prompt_name,
    prompt_version: detail.prompt_version,
    metrics: detail.metrics || [],
    quality_score: detail.quality_score || 0,
    pass_rate: detail.pass_rate || 0,
    avg_latency_ms: detail.avg_latency_ms || 0,
    p95_latency_ms: detail.p95_latency_ms ?? null,
    total_tokens: detail.total_tokens || 0,
    estimated_cost: detail.estimated_cost ?? null,
    result_status: detail.result_status || detail.regression_status || "PASS",
    regression_status: detail.result_status || detail.regression_status || "PASS",
    status: detail.status,
    created_at: detail.created_at,
  };

  return {
    experiment,
    metric_breakdown,
    category_performance,
    quality_trend,
    cases,
  };
}

/** GET /api/v1/dashboard */
export function getDashboardSummary(): Promise<DashboardSummary> {
  return apiFetch<DashboardSummary>("/dashboard");
}
