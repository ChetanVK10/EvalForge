import { useQuery } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { listDatasets } from "@/api/datasets";
import { listExperiments } from "@/api/experiments";
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
        content: "Searchable history of evaluation runs with quality, latency and cost.",
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
  const [search, setSearch] = useState(q ?? "");
  const [datasetId, setDatasetId] = useState("all");
  const [provider, setProvider] = useState<Provider | "all">("all");
  const [model, setModel] = useState("all");
  const [promptVersion, setPromptVersion] = useState("all");
  const [status, setStatus] = useState<RegressionStatus | "all">("all");
  const [since, setSince] = useState("");
  const [selected, setSelected] = useState<string[]>([]);

  const datasets = useQuery({ queryKey: ["datasets"], queryFn: listDatasets });
  const filters = {
    search,
    dataset_id: datasetId,
    provider,
    model,
    prompt_version: promptVersion,
    status,
    ...(since ? { since } : {}),
  };
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["experiments", filters],
    queryFn: () => listExperiments(filters),
  });

  const allModels = [...new Set((data ?? []).map((e) => e.model))];

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

  const selectCls = "h-9 rounded-sm border border-input bg-transparent px-2 text-sm";

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
          value={since}
          onChange={(e) => setSince(e.target.value)}
          className="h-9 w-40"
          aria-label="Created after"
        />
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
        {data && data.length === 0 && (
          <EmptyState className="m-4" title="No experiments match these filters" />
        )}
        {data && data.length > 0 && (
          <ExperimentTable
            experiments={data}
            selectable
            selected={selected}
            onToggleSelect={toggle}
          />
        )}
      </div>
    </div>
  );
}
