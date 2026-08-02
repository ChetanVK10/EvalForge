import { ApiError, notFound, request } from "./client";
import { datasetDetails, datasets } from "@/mocks/data";
import type { CreateDatasetPayload, Dataset, DatasetDetail, EvaluationCase } from "@/types";

const store: DatasetDetail[] = [...datasetDetails];

/** GET /api/v1/datasets */
export function listDatasets(): Promise<Dataset[]> {
  return request("/datasets", () =>
    store.map(({ cases: _cases, ...rest }) => ({ ...rest, case_count: _cases.length })),
  );
}

/** GET /api/v1/datasets/{id} */
export function getDataset(id: string): Promise<DatasetDetail> {
  return request(`/datasets/${id}`, () => {
    const found = store.find((d) => d.id === id);
    if (!found) notFound("Dataset", id);
    return { ...found, case_count: found.cases.length };
  });
}

/** POST /api/v1/datasets */
export function createDataset(payload: CreateDatasetPayload): Promise<Dataset> {
  return request("/datasets", () => {
    if (!payload.name.trim()) throw new ApiError("Dataset name is required.", 422);
    const now = new Date().toISOString();
    const id = `ds-${payload.name
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .slice(0, 24)}`;
    const cases: EvaluationCase[] = payload.cases.map((c, i) => ({
      ...c,
      id: `${id}-case-${String(i + 1).padStart(3, "0")}`,
    }));
    const detail: DatasetDetail = {
      id,
      name: payload.name,
      description: payload.description,
      case_count: cases.length,
      categories: [...new Set(cases.map((c) => c.category))],
      created_at: now,
      updated_at: now,
      cases,
    };
    store.unshift(detail);
    const { cases: _c, ...rest } = detail;
    return rest;
  });
}

/** POST /api/v1/datasets/{id}/cases */
export function addCase(
  datasetId: string,
  payload: Omit<EvaluationCase, "id">,
): Promise<EvaluationCase> {
  return request(`/datasets/${datasetId}/cases`, () => {
    const dataset = store.find((d) => d.id === datasetId);
    if (!dataset) notFound("Dataset", datasetId);
    const newCase: EvaluationCase = {
      ...payload,
      id: `${datasetId}-case-${Date.now().toString(36)}`,
    };
    dataset.cases = [newCase, ...dataset.cases];
    dataset.case_count = dataset.cases.length;
    dataset.updated_at = new Date().toISOString();
    if (!dataset.categories.includes(newCase.category)) {
      dataset.categories = [...dataset.categories, newCase.category];
    }
    return newCase;
  });
}

/** PUT /api/v1/datasets/{id}/cases/{caseId} */
export function updateCase(
  datasetId: string,
  caseId: string,
  payload: Omit<EvaluationCase, "id">,
): Promise<EvaluationCase> {
  return request(`/datasets/${datasetId}/cases/${caseId}`, () => {
    const dataset = store.find((d) => d.id === datasetId);
    if (!dataset) notFound("Dataset", datasetId);
    const index = dataset.cases.findIndex((c) => c.id === caseId);
    if (index === -1) notFound("Evaluation case", caseId);
    const updated: EvaluationCase = { ...payload, id: caseId };
    dataset.cases = dataset.cases.map((c) => (c.id === caseId ? updated : c));
    dataset.updated_at = new Date().toISOString();
    return updated;
  });
}

/** DELETE /api/v1/datasets/{id}/cases/{caseId} */
export function deleteCase(datasetId: string, caseId: string): Promise<{ id: string }> {
  return request(`/datasets/${datasetId}/cases/${caseId}`, () => {
    const dataset = store.find((d) => d.id === datasetId);
    if (!dataset) notFound("Dataset", datasetId);
    dataset.cases = dataset.cases.filter((c) => c.id !== caseId);
    dataset.case_count = dataset.cases.length;
    dataset.updated_at = new Date().toISOString();
    return { id: caseId };
  });
}

/** POST /api/v1/datasets/{id}/import (JSONL body) */
export function importJsonl(datasetId: string, contents: string): Promise<{ imported: number }> {
  return request(`/datasets/${datasetId}/import`, () => {
    const dataset = store.find((d) => d.id === datasetId);
    if (!dataset) notFound("Dataset", datasetId);
    const lines = contents
      .split("\n")
      .map((l) => l.trim())
      .filter(Boolean);
    if (lines.length === 0) throw new ApiError("The uploaded file contained no rows.", 422);

    const parsed: EvaluationCase[] = [];
    lines.forEach((line, i) => {
      let row: Partial<EvaluationCase>;
      try {
        row = JSON.parse(line) as Partial<EvaluationCase>;
      } catch {
        throw new ApiError(`Line ${i + 1} is not valid JSON.`, 422);
      }
      if (!row.input || !row.expected_output) {
        throw new ApiError(`Line ${i + 1} is missing "input" or "expected_output".`, 422);
      }
      parsed.push({
        id: `${datasetId}-case-import-${Date.now().toString(36)}-${i}`,
        input: row.input,
        expected_output: row.expected_output,
        category: row.category ?? "general",
        metadata: row.metadata ?? {},
      });
    });

    dataset.cases = [...parsed, ...dataset.cases];
    dataset.case_count = dataset.cases.length;
    dataset.updated_at = new Date().toISOString();
    return { imported: parsed.length };
  });
}
