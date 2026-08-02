import { notFound, request } from "./client";
import {
  experiments as mockExperiments,
  getCaseResults,
  getCategoryScores,
  getMetricBreakdown,
} from "@/mocks/data";
import type {
  DashboardSummary,
  Experiment,
  ExperimentFilters,
  ExperimentResult,
  MetricResult,
} from "@/types";

const store: Experiment[] = [...mockExperiments];

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

export function registerExperiment(experiment: Experiment): void {
  store.unshift(experiment);
}

/** GET /api/v1/experiments */
export function listExperiments(filters: ExperimentFilters = {}): Promise<Experiment[]> {
  return request("/experiments", () => {
    const search = filters.search?.trim().toLowerCase();
    return store
      .filter((e) => {
        if (search && !`${e.name} ${e.model} ${e.prompt_name}`.toLowerCase().includes(search)) {
          return false;
        }
        if (
          filters.dataset_id &&
          filters.dataset_id !== "all" &&
          e.dataset_id !== filters.dataset_id
        )
          return false;
        if (filters.provider && filters.provider !== "all" && e.provider !== filters.provider)
          return false;
        if (filters.model && filters.model !== "all" && e.model !== filters.model) return false;
        if (
          filters.prompt_version &&
          filters.prompt_version !== "all" &&
          String(e.prompt_version) !== filters.prompt_version
        )
          return false;
        if (filters.status && filters.status !== "all" && e.regression_status !== filters.status)
          return false;
        if (filters.since && new Date(e.created_at) < new Date(filters.since)) return false;
        return true;
      })
      .sort((a, b) => +new Date(b.created_at) - +new Date(a.created_at));
  });
}

/** GET /api/v1/experiments/{id} */
export function getExperiment(id: string): Promise<Experiment> {
  return request(`/experiments/${id}`, () => {
    const found = store.find((e) => e.id === id);
    if (!found) notFound("Experiment", id);
    return found;
  });
}

/** GET /api/v1/experiments/{id}/results */
export function getExperimentResult(id: string): Promise<ExperimentResult> {
  return request(`/experiments/${id}/results`, () => {
    const experiment = store.find((e) => e.id === id);
    if (!experiment) notFound("Experiment", id);
    const cases = getCaseResults(id);
    const categoryScores = getCategoryScores(id);
    const category_performance: MetricResult[] = Object.entries(categoryScores).map(
      ([key, score]) => ({
        key,
        label: categoryLabels[key] ?? key,
        score: score as number,
      }),
    );

    const bucketSize = Math.max(1, Math.ceil(cases.length / 8));
    const quality_trend = Array.from({ length: Math.ceil(cases.length / bucketSize) }, (_, i) => {
      const bucket = cases.slice(i * bucketSize, (i + 1) * bucketSize);
      const avg = bucket.reduce((sum, c) => sum + c.score, 0) / (bucket.length || 1);
      return { date: `Batch ${i + 1}`, score: Number(avg.toFixed(1)) };
    });

    return {
      experiment,
      metric_breakdown: getMetricBreakdown(id),
      category_performance,
      quality_trend,
      cases,
    };
  });
}

/** GET /api/v1/dashboard */
export function getDashboardSummary(): Promise<DashboardSummary> {
  return request("/dashboard", () => {
    const sorted = [...store].sort((a, b) => +new Date(a.created_at) - +new Date(b.created_at));
    const total = store.length;
    const avg = (nums: number[]) =>
      Number((nums.reduce((s, n) => s + n, 0) / (nums.length || 1)).toFixed(1));

    const weekAgo = new Date("2026-08-02T00:00:00Z").getTime() - 7 * 864e5;
    const thisWeek = store.filter((e) => +new Date(e.created_at) >= weekAgo).length;
    const passing = store.filter((e) => e.regression_status === "PASS").length;

    const fmt = (iso: string) =>
      new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric" });

    return {
      total_experiments: total,
      evaluations_this_week: thisWeek,
      avg_quality_score: avg(store.map((e) => e.quality_score)),
      avg_latency_ms: Math.round(avg(store.map((e) => e.avg_latency_ms))),
      estimated_cost: Number(store.reduce((s, e) => s + e.estimated_cost, 0).toFixed(2)),
      regression_pass_rate: Number(((passing / (total || 1)) * 100).toFixed(1)),
      quality_over_time: sorted.map((e) => ({ date: fmt(e.created_at), score: e.quality_score })),
      latency_over_time: sorted.map((e) => ({
        date: fmt(e.created_at),
        latency: e.avg_latency_ms,
      })),
      cost_over_time: sorted.map((e) => ({ date: fmt(e.created_at), cost: e.estimated_cost })),
      recent_experiments: [...store]
        .sort((a, b) => +new Date(b.created_at) - +new Date(a.created_at))
        .slice(0, 6),
      alerts: [
        {
          id: "alert-1",
          severity: "FAIL",
          message:
            "Customer Support prompt v4 decreased factuality by 8.2% compared with v3, exceeding the 3% regression threshold.",
          experiment_id: "exp-014",
          created_at: "2026-07-31T09:31:00Z",
        },
        {
          id: "alert-2",
          severity: "FAIL",
          message:
            "Billing category regressed 13.4% on prompt v4 — billing is a critical category and blocks promotion.",
          experiment_id: "exp-014",
          created_at: "2026-07-31T09:31:00Z",
        },
        {
          id: "alert-3",
          severity: "WARNING",
          message:
            "Groq Llama 8B latency probe scored 82.7% overall, 8.5% below the 70B production baseline.",
          experiment_id: "exp-011",
          created_at: "2026-07-25T08:40:00Z",
        },
        {
          id: "alert-4",
          severity: "WARNING",
          message:
            "Incident Summarizer v3 pass rate dropped to 83.3% on instruction-following cases.",
          experiment_id: "exp-008",
          created_at: "2026-07-15T17:02:00Z",
        },
      ],
    };
  });
}
