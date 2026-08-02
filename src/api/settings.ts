import { request } from "./client";
import { settings as mockSettings } from "@/mocks/data";
import type { EvaluationDefaults, RegressionThresholds, Settings } from "@/types";

const state: Settings = {
  evaluation_defaults: { ...mockSettings.evaluation_defaults },
  regression_thresholds: { ...mockSettings.regression_thresholds },
  providers: mockSettings.providers.map((p) => ({ ...p })),
};

/** GET /api/v1/settings */
export function getSettings(): Promise<Settings> {
  return request("/settings", () => ({
    evaluation_defaults: { ...state.evaluation_defaults },
    regression_thresholds: { ...state.regression_thresholds },
    providers: state.providers.map((p) => ({ ...p })),
  }));
}

/** GET /api/v1/settings/regression */
export function getRegressionThresholds(): Promise<RegressionThresholds> {
  return request("/settings/regression", () => ({ ...state.regression_thresholds }));
}

/** PUT /api/v1/settings/regression */
export function updateRegressionThresholds(
  payload: RegressionThresholds,
): Promise<RegressionThresholds> {
  return request("/settings/regression", () => {
    state.regression_thresholds = { ...payload };
    return { ...state.regression_thresholds };
  });
}

/** PUT /api/v1/settings/evaluation */
export function updateEvaluationDefaults(payload: EvaluationDefaults): Promise<EvaluationDefaults> {
  return request("/settings/evaluation", () => {
    state.evaluation_defaults = { ...payload };
    return { ...state.evaluation_defaults };
  });
}
