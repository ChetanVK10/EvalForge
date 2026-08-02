import { ApiError, notFound, request } from "./client";
import { modelConfigurations, promptConfigurations } from "@/mocks/data";
import type {
  CreateModelConfigurationPayload,
  ModelConfiguration,
  PromptConfiguration,
  PromptStatus,
  PromptVersion,
} from "@/types";

const models: ModelConfiguration[] = [...modelConfigurations];
const prompts: PromptConfiguration[] = promptConfigurations.map((p) => ({
  ...p,
  versions: [...p.versions],
}));

/** GET /api/v1/configurations/models */
export function listModelConfigurations(): Promise<ModelConfiguration[]> {
  return request("/configurations/models", () => [...models]);
}

/** POST /api/v1/configurations/models */
export function createModelConfiguration(
  payload: CreateModelConfigurationPayload,
): Promise<ModelConfiguration> {
  return request("/configurations/models", () => {
    if (!payload.name.trim()) throw new ApiError("Configuration name is required.", 422);
    if (!payload.model.trim()) throw new ApiError("Model is required.", 422);
    const created: ModelConfiguration = {
      ...payload,
      id: `mc-${Date.now().toString(36)}`,
      created_at: new Date().toISOString(),
    };
    models.unshift(created);
    return created;
  });
}

/** GET /api/v1/prompts */
export function listPromptConfigurations(): Promise<PromptConfiguration[]> {
  return request("/prompts", () => prompts.map((p) => ({ ...p, versions: [...p.versions] })));
}

/** GET /api/v1/prompts/{id} */
export function getPromptConfiguration(id: string): Promise<PromptConfiguration> {
  return request(`/prompts/${id}`, () => {
    const found = prompts.find((p) => p.id === id);
    if (!found) notFound("Prompt configuration", id);
    return { ...found, versions: [...found.versions] };
  });
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
  return request("/prompts", () => {
    if (!payload.name.trim()) throw new ApiError("Prompt name is required.", 422);
    if (!payload.system_prompt.trim()) throw new ApiError("System prompt is required.", 422);
    const now = new Date().toISOString();
    const id = `pc-${Date.now().toString(36)}`;
    const created: PromptConfiguration = {
      id,
      name: payload.name,
      status: payload.status,
      latest_version: 1,
      created_at: now,
      versions: [
        {
          id: `${id}-v1`,
          version: 1,
          system_prompt: payload.system_prompt,
          user_template: payload.user_template,
          notes: payload.notes,
          created_at: now,
        },
      ],
    };
    prompts.unshift(created);
    return created;
  });
}

/** POST /api/v1/prompts/{id}/versions */
export function createPromptVersion(
  promptId: string,
  payload: Omit<CreatePromptPayload, "name" | "status">,
): Promise<PromptVersion> {
  return request(`/prompts/${promptId}/versions`, () => {
    const prompt = prompts.find((p) => p.id === promptId);
    if (!prompt) notFound("Prompt configuration", promptId);
    const version = prompt.latest_version + 1;
    const created: PromptVersion = {
      id: `${promptId}-v${version}`,
      version,
      system_prompt: payload.system_prompt,
      user_template: payload.user_template,
      notes: payload.notes,
      created_at: new Date().toISOString(),
    };
    prompt.versions = [...prompt.versions, created];
    prompt.latest_version = version;
    return created;
  });
}

/** PUT /api/v1/prompts/{id}/versions/{version} */
export function updatePromptVersion(
  promptId: string,
  version: number,
  payload: Omit<CreatePromptPayload, "name" | "status">,
): Promise<PromptVersion> {
  return request(`/prompts/${promptId}/versions/${version}`, () => {
    const prompt = prompts.find((p) => p.id === promptId);
    if (!prompt) notFound("Prompt configuration", promptId);
    const existing = prompt.versions.find((v) => v.version === version);
    if (!existing) notFound("Prompt version", String(version));
    const updated: PromptVersion = { ...existing, ...payload };
    prompt.versions = prompt.versions.map((v) => (v.version === version ? updated : v));
    return updated;
  });
}
