import { ApiError, delay, notFound, request } from "./client";
import {
  breakdown,
  datasetDetails,
  modelConfigurations,
  promptConfigurations,
  registerExperimentSeed,
} from "@/mocks/data";
import { registerExperiment } from "./experiments";
import type {
  CreateEvaluationPayload,
  EvaluationCategory,
  EvaluationProgress,
  Experiment,
} from "@/types";

/**
 * Simulated evaluation execution.
 *
 * The FastAPI backend will expose `POST /api/v1/evaluations` returning a job id
 * plus a polling/stream endpoint. Only this module changes at that point — the
 * `onProgress` callback signature is intentionally poll-friendly.
 */
export async function runEvaluation(
  payload: CreateEvaluationPayload,
  onProgress: (progress: EvaluationProgress) => void,
): Promise<Experiment> {
  const dataset = datasetDetails.find((d) => d.id === payload.dataset_id);
  const modelConfig = modelConfigurations.find((m) => m.id === payload.model_config_id);
  const prompt = promptConfigurations.find((p) => p.id === payload.prompt_id);

  if (!payload.name.trim()) throw new ApiError("Experiment name is required.", 422);
  if (!dataset) notFound("Dataset", payload.dataset_id);
  if (!modelConfig) notFound("Model configuration", payload.model_config_id);
  if (!prompt) notFound("Prompt configuration", payload.prompt_id);
  if (payload.metrics.length === 0)
    throw new ApiError("Select at least one evaluation metric.", 422);

  const total = dataset.cases.length;

  onProgress({ stage: "preparing", message: "Preparing evaluation…", completed: 0, total });
  await delay(700);

  const step = Math.max(1, Math.round(total / 12));
  for (let done = step; done < total; done += step) {
    onProgress({
      stage: "running",
      message: `Running ${done} / ${total} cases`,
      completed: done,
      total,
    });
    await delay(220);
  }
  onProgress({
    stage: "running",
    message: `Running ${total} / ${total} cases`,
    completed: total,
    total,
  });
  await delay(300);

  onProgress({ stage: "scoring", message: "Calculating metrics…", completed: total, total });
  await delay(650);

  const experiment = await request("/evaluations", () => {
    const version =
      prompt.versions.find((v) => v.version === payload.prompt_version) ?? prompt.versions[0]!;

    // Deterministic scoring derived from configuration, never Math.random.
    const base =
      82 +
      (modelConfig.model.includes("70b") ? 6 : modelConfig.provider === "gemini" ? 5 : 0) +
      version.version * 0.9 -
      modelConfig.temperature * 4;
    const quality = Number(Math.min(97, base).toFixed(1));
    const latency = Math.round(
      (modelConfig.model.includes("8b") ? 320 : modelConfig.provider === "gemini" ? 1100 : 800) *
        (1 + modelConfig.max_tokens / 8000),
    );
    const tokens = Math.round(total * (modelConfig.max_tokens * 0.42 + 900));
    const cost = Number(
      (tokens * (modelConfig.provider === "gemini" ? 0.0000025 : 0.0000019)).toFixed(2),
    );

    const id = `exp-${Date.now().toString(36)}`;
    const categories = dataset.categories.reduce<Partial<Record<EvaluationCategory, number>>>(
      (acc, category, i) => {
        acc[category] = Number((quality + (i % 2 === 0 ? 1.8 : -2.1) - i * 0.6).toFixed(1));
        return acc;
      },
      {},
    );

    const created: Experiment = {
      id,
      name: payload.name,
      dataset_id: dataset.id,
      dataset_name: dataset.name,
      model_config_id: modelConfig.id,
      provider: modelConfig.provider,
      model: modelConfig.model,
      prompt_id: prompt.id,
      prompt_name: prompt.name,
      prompt_version: version.version,
      metrics: payload.metrics,
      quality_score: quality,
      pass_rate: Number((quality - 3.1).toFixed(1)),
      avg_latency_ms: latency,
      p95_latency_ms: Math.round(latency * 1.68),
      total_tokens: tokens,
      estimated_cost: cost,
      regression_status: quality >= 90 ? "PASS" : quality >= 85 ? "WARNING" : "FAIL",
      status: "completed",
      created_at: new Date().toISOString(),
    };

    registerExperimentSeed({
      ...created,
      metric_breakdown: breakdown({
        factuality: Number((quality + 1.2).toFixed(1)),
        reasoning: Number((quality - 1.4).toFixed(1)),
        completeness: Number((quality + 0.6).toFixed(1)),
        instruction: Number((quality - 0.3).toFixed(1)),
      }),
      category_scores: categories,
    });
    registerExperiment(created);
    return created;
  });

  onProgress({ stage: "complete", message: "Evaluation complete", completed: total, total });
  return experiment;
}
