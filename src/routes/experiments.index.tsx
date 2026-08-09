import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { listDatasets } from "@/api/datasets";
import { deleteExperiment, listExperiments } from "@/api/experiments";
import { PageHeader } from "@/components/common/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/States";
import { ExperimentTable } from "@/components/experiments/ExperimentTable";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import type { Provider, RegressionStatus } from "@/types";

interface ExperimentSearch {
  q?: string;
}

export const Route = createFileRoute("/experiments/")({
  validateSearch: (search: Record<string, unknown>): ExperimentSearch => {
    const q = search["q"];
    return typeof q === "string" && q ? { q } : {};
  },
  head: () => ({
    meta: [
      { title: "Experiments — LLMOps Studio" },
      {
        name: "description",
        content:
          "Searchable history of evaluation runs with quality, latency and regression pass rate.",
      },
      { property: "og:title", content: "Experiments — LLMOps Studio" },
      { property: "og:description", content: "Evaluation run history and comparison." },
    ],
  }),
  component: ExperimentsPage,
});

function ExperimentsPage() {
  const { q } = Route.useSearch();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState(q ?? "");
  const [datasetId, setDatasetId] = useState("all");
  const [provider, setProvider] = useState<Provider | "all">("all");
  const [model, setModel] = useState("all");
  const [promptVersion, setPromptVersion] = useState("all");
  const [status, setStatus] = useState<RegressionStatus | "all">("all");
  const [date, setDate] = useState("");
  const [selected, setSelected] = useState<string[]>([]);

  const datasets = useQuery({ queryKey: ["datasets"], queryFn: listDatasets });
  const filters = {
    search,
    dataset_id: datasetId,
    provider,
    model,
    prompt_version: promptVersion,
    status,
    ...(date ? { date } : {}),
  };
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["experiments", filters],
    queryFn: () => listExperiments(filters),
  });

  const allModels = [...new Set((data ?? []).map((e) => e.model))];

  const filteredExperiments = (data ?? []).filter((e) => {
    if (search) {
      const queryStr = search.toLowerCase();
      const matchesName = e.name.toLowerCase().includes(queryStr);
      const matchesId = e.id.toLowerCase().includes(queryStr);
      const matchesDataset = (e.dataset_name || "").toLowerCase().includes(queryStr);
      const matchesPrompt = (e.prompt_name || "").toLowerCase().includes(queryStr);
      const matchesModel = e.model.toLowerCase().includes(queryStr);
      if (!matchesName && !matchesId && !matchesDataset && !matchesPrompt && !matchesModel) {
        return false;
      }
    }
    if (datasetId !== "all" && e.dataset_id !== datasetId) return false;
    if (provider !== "all" && e.provider.toLowerCase() !== provider.toLowerCase()) return false;
    if (model !== "all" && e.model.toLowerCase() !== model.toLowerCase()) return false;
    if (promptVersion !== "all" && String(e.prompt_version) !== String(promptVersion)) return false;
    if (
      status !== "all" &&
      (e.result_status || e.regression_status).toUpperCase() !== status.toUpperCase()
    )
      return false;
    if (date) {
      const expDateStr = e.created_at.slice(0, 10);
      if (expDateStr !== date) return false;
    }
    return true;
  });

  const hasActiveFilters =
    search !== "" ||
    datasetId !== "all" ||
    provider !== "all" ||
    model !== "all" ||
    promptVersion !== "all" ||
    status !== "all" ||
    date !== "";

  const resetFilters = () => {
    setSearch("");
    setDatasetId("all");
    setProvider("all");
    setModel("all");
    setPromptVersion("all");
    setStatus("all");
    setDate("");
  };

  const toggle = (id: string) =>
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id].slice(-2),
    );

  const compare = () => {
    if (selected.length !== 2) {
      toast.error("Select exactly two experiments to compare.");
      return;
    }
    const [a, b] = selected;
    void navigate({
      to: "/regression",
      search: { baseline: a as string, candidate: b as string },
    });
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteExperiment(id);
      toast.success("Experiment deleted successfully.");
      setSelected((prev) => prev.filter((x) => x !== id));
      void queryClient.invalidateQueries({ queryKey: ["experiments"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    } catch (err: any) {
      toast.error(err.message || "Failed to delete experiment.");
    }
  };

  const selectCls =
    "h-9 rounded-sm border border-input bg-transparent px-2 pr-7 text-sm max-w-full min-w-0 truncate cursor-pointer";

  return (
    <div className="space-y-6">
      <PageHeader
        title="Experiments"
        description="Every evaluation run in this workspace. Select two runs on the same dataset to compare them for regressions."
        actions={
          <Button size="sm" onClick={compare} disabled={selected.length !== 2}>
            Compare ({selected.length}/2)
          </Button>
        }
      />

      <div className="panel flex flex-wrap items-center gap-2 p-3">
        <Input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search experiments…"
          className="h-9 w-56"
          aria-label="Search experiments"
        />
        <select
          className={selectCls}
          value={datasetId}
          onChange={(e) => setDatasetId(e.target.value)}
          aria-label="Dataset filter"
        >
          <option value="all">All datasets</option>
          {datasets.data?.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
        <select
          className={selectCls}
          value={provider}
          onChange={(e) => setProvider(e.target.value as Provider | "all")}
          aria-label="Provider filter"
        >
          <option value="all">All providers</option>
          <option value="groq">Groq</option>
          <option value="gemini">Gemini</option>
        </select>
        <select
          className={selectCls}
          value={model}
          onChange={(e) => setModel(e.target.value)}
          aria-label="Model filter"
        >
          <option value="all">All models</option>
          {allModels.map((m) => (
            <option key={m} value={m}>
              {m}
            </option>
          ))}
        </select>
        <select
          className={selectCls}
          value={promptVersion}
          onChange={(e) => setPromptVersion(e.target.value)}
          aria-label="Prompt version filter"
        >
          <option value="all">All versions</option>
          {[1, 2, 3, 4].map((v) => (
            <option key={v} value={String(v)}>
              v{v}
            </option>
          ))}
        </select>
        <select
          className={selectCls}
          value={status}
          onChange={(e) => setStatus(e.target.value as RegressionStatus | "all")}
          aria-label="Status filter"
        >
          <option value="all">All statuses</option>
          <option value="PASS">PASS</option>
          <option value="WARNING">WARNING</option>
          <option value="FAIL">FAIL</option>
        </select>
        <Input
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
          className="h-9 w-40"
          aria-label="Filter by date"
        />
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={resetFilters} className="h-9 text-xs">
            Reset filters
          </Button>
        )}
      </div>

      <div className="panel">
        {isLoading && <LoadingState rows={8} />}
        {isError && (
          <ErrorState
            className="m-4"
            message={(error as Error).message}
            onRetry={() => void refetch()}
          />
        )}
        {data && filteredExperiments.length === 0 && (
          <EmptyState className="m-4" title="No experiments match these filters" />
        )}
        {data && filteredExperiments.length > 0 && (
          <ExperimentTable
            experiments={filteredExperiments}
            selectable
            selected={selected}
            onToggleSelect={toggle}
            onDelete={handleDelete}
          />
        )}
      </div>
    </div>
  );
}
