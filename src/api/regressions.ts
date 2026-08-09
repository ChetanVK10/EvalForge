import { apiFetch } from "./client";
import type { RegressionComparison } from "@/types";

export interface CompareRequest {
  baseline_experiment_id: string;
  candidate_experiment_id: string;
}

/** POST /api/v1/regressions/compare */
export function compareExperiments(payload: CompareRequest): Promise<RegressionComparison> {
  if (!payload.baseline_experiment_id || !payload.candidate_experiment_id) {
    return Promise.reject(new Error("Both baseline and candidate experiments must be selected."));
  }

  if (payload.baseline_experiment_id === payload.candidate_experiment_id) {
    return Promise.reject(new Error("Baseline and candidate must be different experiments."));
  }

  return apiFetch<RegressionComparison>("/regressions/compare", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}
