import { apiFetch } from "./client";
import type { EvaluationDefaults, RegressionThresholds, Settings } from "@/types";

/** GET /api/v1/settings */
export function getSettings(): Promise<Settings> {
  return apiFetch<Settings>("/settings");
}

/** GET /api/v1/settings/regression */
export function getRegressionThresholds(): Promise<RegressionThresholds> {
  return apiFetch<RegressionThresholds>("/settings/regression");
}

/** PUT /api/v1/settings/regression */
export function updateRegressionThresholds(
  payload: RegressionThresholds,
): Promise<RegressionThresholds> {
  return apiFetch<RegressionThresholds>("/settings/regression", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

/** PUT /api/v1/settings/evaluation */
export function updateEvaluationDefaults(payload: EvaluationDefaults): Promise<EvaluationDefaults> {
  return apiFetch<EvaluationDefaults>("/settings/evaluation", {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}
