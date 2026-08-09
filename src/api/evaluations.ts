import { apiFetch, delay } from "./client";
import { getExperiment } from "./experiments";
import type { CreateEvaluationPayload, EvaluationProgress, Experiment } from "@/types";

export interface EvaluationStatusResponse {
  experiment_id: string;
  status: string;
  stage: "preparing" | "running" | "scoring" | "complete" | "failed";
  message: string;
  total_cases: number;
  completed_cases: number;
  failed_cases: number;
  progress_pct: number;
}

/**
 * Executes a real evaluation run against the FastAPI backend and polls for progress.
 */
export async function runEvaluation(
  payload: CreateEvaluationPayload,
  onProgress: (progress: EvaluationProgress) => void,
): Promise<Experiment> {
  // 1. Submit evaluation creation request to FastAPI backend
  const createdExperiment = await apiFetch<Experiment>("/evaluations", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  onProgress({
    stage: "preparing",
    message: "Preparing evaluation run…",
    completed: 0,
    total: 100,
  });

  // 2. Poll progress status endpoint until completion or failure
  const expId = createdExperiment.id;
  let isDone = false;
  let pollAttempts = 0;
  const maxPollAttempts = 120; // 4 minutes max polling limit

  while (!isDone && pollAttempts < maxPollAttempts) {
    await delay(1500);
    pollAttempts++;

    try {
      const statusRes = await apiFetch<EvaluationStatusResponse>(`/evaluations/${expId}/status`);
      const total = statusRes.total_cases || 1;
      const done = statusRes.completed_cases + statusRes.failed_cases;

      onProgress({
        stage:
          statusRes.stage === "complete"
            ? "complete"
            : statusRes.stage === "failed"
              ? "complete"
              : statusRes.stage,
        message: statusRes.message,
        completed: done,
        total,
      });

      if (statusRes.status === "completed" || statusRes.status === "failed") {
        isDone = true;
      }
    } catch {
      // Continue polling if transient status check fails
    }
  }

  // 3. Retrieve final persisted experiment object
  const finalExperiment = await getExperiment(expId);
  return finalExperiment;
}
