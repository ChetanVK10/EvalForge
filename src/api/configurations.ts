import { apiFetch } from "./client";
import type {
  CreateModelConfigurationPayload,
  ModelConfiguration,
  PromptConfiguration,
  PromptStatus,
  PromptVersion,
} from "@/types";

/** GET /api/v1/configurations/models */
export function listModelConfigurations(): Promise<ModelConfiguration[]> {
  return apiFetch<ModelConfiguration[]>("/configurations/models");
}

/** POST /api/v1/configurations/models */
export function createModelConfiguration(
  payload: CreateModelConfigurationPayload,
): Promise<ModelConfiguration> {
  return apiFetch<ModelConfiguration>("/configurations/models", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export interface UpdateModelConfigurationPayload {
  name: string;
  model: string;
  temperature: number;
  max_tokens: number;
}

/** PUT /api/v1/configurations/models/{id} */
export function updateModelConfiguration(
  id: string,
  payload: UpdateModelConfigurationPayload,
): Promise<ModelConfiguration> {
  return apiFetch<ModelConfiguration>(`/configurations/models/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

/** GET /api/v1/prompts */
export function listPromptConfigurations(): Promise<PromptConfiguration[]> {
  return apiFetch<PromptConfiguration[]>("/prompts");
}

/** GET /api/v1/prompts/{id} */
export function getPromptConfiguration(id: string): Promise<PromptConfiguration> {
  return apiFetch<PromptConfiguration>(`/prompts/${id}`);
}

export interface CreatePromptPayload {
  name: string;
  status: PromptStatus;
  system_prompt: string;
  user_template: string;
  notes: string;
}

/** POST /api/v1/prompts */
export function createPromptConfiguration(
  payload: CreatePromptPayload,
): Promise<PromptConfiguration> {
  return apiFetch<PromptConfiguration>("/prompts", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** POST /api/v1/prompts/{id}/versions */
export function createPromptVersion(
  promptId: string,
  payload: Omit<CreatePromptPayload, "name" | "status">,
): Promise<PromptVersion> {
  return apiFetch<PromptVersion>(`/prompts/${promptId}/versions`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** PUT /api/v1/prompts/{id}/versions/{version} */
export function updatePromptVersion(
  promptId: string,
  version: number,
  payload: Omit<CreatePromptPayload, "name" | "status">,
): Promise<PromptVersion> {
  return apiFetch<PromptVersion>(`/prompts/${promptId}/versions/${version}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export interface UpdatePromptConfigurationPayload {
  name: string;
}

/** PUT /api/v1/prompts/{id} */
export function updatePromptConfiguration(
  id: string,
  payload: UpdatePromptConfigurationPayload,
): Promise<PromptConfiguration> {
  return apiFetch<PromptConfiguration>(`/prompts/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}
/** DELETE /api/v1/configurations/models/{id} */
export function deleteModelConfiguration(id: string): Promise<void> {
  return apiFetch<void>(`/configurations/models/${id}`, {
    method: "DELETE",
  });
}

/** DELETE /api/v1/configurations/prompts/{id} */
export function deletePromptConfiguration(id: string): Promise<void> {
  return apiFetch<void>(`/configurations/prompts/${id}`, {
    method: "DELETE",
  });
}
