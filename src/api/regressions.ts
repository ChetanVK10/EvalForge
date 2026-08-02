import { ApiError, notFound, request } from "./client";
import { computeComparison } from "@/lib/regression";
import { getCaseResults, getCategoryScores, getMetricBreakdown } from "@/mocks/data";
import { getExperiment } from "./experiments";
import { getRegressionThresholds } from "./settings";
import type { RegressionComparison } from "@/types";

export interface CompareRequest {
  baseline_experiment_id: string;
  candidate_experiment_id: string;
}

/** POST /api/v1/regressions/compare */
export async function compareExperiments({
  baseline_experiment_id,
  candidate_experiment_id,
}: CompareRequest): Promise<RegressionComparison> {
  if (baseline_experiment_id === candidate_experiment_id) {
    throw new ApiError("Baseline and candidate must be different experiments.", 422);
  }
  const [baseline, candidate, thresholds] = await Promise.all([
    getExperiment(baseline_experiment_id),
    getExperiment(candidate_experiment_id),
    getRegressionThresholds(),
  ]);

  return request("/regressions/compare", () => {
    if (baseline.dataset_id !== candidate.dataset_id) {
      throw new ApiError(
        "Experiments must run on the same dataset to be compared for regressions.",
        422,
      );
    }
    if (!baseline || !candidate) notFound("Experiment", baseline_experiment_id);
    return computeComparison({
      baseline,
      candidate,
      baselineBreakdown: getMetricBreakdown(baseline.id),
      candidateBreakdown: getMetricBreakdown(candidate.id),
      baselineCategories: getCategoryScores(baseline.id),
      candidateCategories: getCategoryScores(candidate.id),
      baselineCases: getCaseResults(baseline.id),
      candidateCases: getCaseResults(candidate.id),
      thresholds,
    });
  });
}

/** The demo scenario surfaced by default on the Regression page. */
export const DEFAULT_COMPARISON: CompareRequest = {
  baseline_experiment_id: "exp-013",
  candidate_experiment_id: "exp-014",
};
