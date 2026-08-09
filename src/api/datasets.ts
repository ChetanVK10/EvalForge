import { apiFetch } from "./client";
import type { CreateDatasetPayload, Dataset, DatasetDetail, EvaluationCase } from "@/types";

/** GET /api/v1/datasets */
export function listDatasets(): Promise<Dataset[]> {
  return apiFetch<Dataset[]>("/datasets");
}

/** GET /api/v1/datasets/{id} */
export function getDataset(id: string): Promise<DatasetDetail> {
  return apiFetch<DatasetDetail>(`/datasets/${id}`);
}

/** POST /api/v1/datasets */
export function createDataset(payload: CreateDatasetPayload): Promise<Dataset> {
  return apiFetch<Dataset>("/datasets", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export interface UpdateDatasetPayload {
  name: string;
  description?: string;
}

/** PUT /api/v1/datasets/{id} */
export function updateDataset(id: string, payload: UpdateDatasetPayload): Promise<Dataset> {
  return apiFetch<Dataset>(`/datasets/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

/** POST /api/v1/datasets/{id}/cases */
export function addCase(
  datasetId: string,
  payload: Omit<EvaluationCase, "id">,
): Promise<EvaluationCase> {
  return apiFetch<EvaluationCase>(`/datasets/${datasetId}/cases`, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** PUT /api/v1/datasets/{id}/cases/{caseId} */
export function updateCase(
  datasetId: string,
  caseId: string,
  payload: Omit<EvaluationCase, "id">,
): Promise<EvaluationCase> {
  return apiFetch<EvaluationCase>(`/datasets/${datasetId}/cases/${caseId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

/** DELETE /api/v1/datasets/{id}/cases/{caseId} */
export function deleteCase(datasetId: string, caseId: string): Promise<{ id: string }> {
  return apiFetch<{ id: string }>(`/datasets/${datasetId}/cases/${caseId}`, {
    method: "DELETE",
  });
}

/** POST /api/v1/datasets/{id}/import (JSONL body) */
export function importJsonl(datasetId: string, contents: string): Promise<{ imported: number }> {
  const lines = contents
    .split("\n")
    .map((l) => l.trim())
    .filter(Boolean);

  const cases: Omit<EvaluationCase, "id">[] = [];
  lines.forEach((line, i) => {
    let row: Partial<EvaluationCase>;
    try {
      row = JSON.parse(line) as Partial<EvaluationCase>;
    } catch {
      throw new Error(`Line ${i + 1} is not valid JSON.`);
    }
    if (!row.input || !row.expected_output) {
      throw new Error(`Line ${i + 1} is missing "input" or "expected_output".`);
    }
    cases.push({
      input: row.input,
      expected_output: row.expected_output,
      category: row.category ?? "general",
      metadata: row.metadata ?? {},
    });
  });

  return apiFetch<{ imported: number }>(`/datasets/${datasetId}/import`, {
    method: "POST",
    body: JSON.stringify({ cases }),
  });
}

/** DELETE /api/v1/datasets/{id} */
export function deleteDataset(id: string): Promise<void> {
  return apiFetch<void>(`/datasets/${id}`, {
    method: "DELETE",
  });
}
