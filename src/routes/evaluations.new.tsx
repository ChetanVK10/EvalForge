import { useQuery } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Play } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { listModelConfigurations, listPromptConfigurations } from "@/api/configurations";
import { listDatasets } from "@/api/datasets";
import { runEvaluation } from "@/api/evaluations";
import { PageHeader, SectionHeader } from "@/components/common/PageHeader";
import { ErrorState, LoadingState } from "@/components/common/States";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { METRIC_OPTIONS } from "@/utils/format";
import type { EvaluationProgress, MetricKey } from "@/types";

export const Route = createFileRoute("/evaluations/new")({
  head: () => ({
    meta: [
      { title: "New Evaluation — LLMOps Studio" },
      {
        name: "description",
        content: "Configure a dataset, model and prompt version, then launch an evaluation run.",
      },
      { property: "og:title", content: "New Evaluation — LLMOps Studio" },
      { property: "og:description", content: "Launch a repeatable LLM evaluation run." },
    ],
  }),
  component: NewEvaluationPage,
});

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between border-b border-border py-2 last:border-0">
      <span className="text-xs text-muted-foreground">{label}</span>
      <span className="num text-sm font-medium">{value}</span>
    </div>
  );
}

function NewEvaluationPage() {
  const navigate = useNavigate();
  const datasets = useQuery({ queryKey: ["datasets"], queryFn: listDatasets });
  const models = useQuery({ queryKey: ["model-configs"], queryFn: listModelConfigurations });
  const prompts = useQuery({ queryKey: ["prompt-configs"], queryFn: listPromptConfigurations });

  const [name, setName] = useState("Support v5 — candidate run");
  const [datasetId, setDatasetId] = useState("ds-support");
  const [modelId, setModelId] = useState("mc-groq-70b");
  const [promptId, setPromptId] = useState("pc-support");
  const [version, setVersion] = useState(4);
  const [metrics, setMetrics] = useState<MetricKey[]>([
    "semantic_similarity",
    "llm_judge",
    "response_completeness",
  ]);
  const [progress, setProgress] = useState<EvaluationProgress | null>(null);
  const [running, setRunning] = useState(false);

  const loading = datasets.isLoading || models.isLoading || prompts.isLoading;
  const failed = datasets.isError || models.isError || prompts.isError;

  const dataset = datasets.data?.find((d) => d.id === datasetId);
  const model = models.data?.find((m) => m.id === modelId);
  const prompt = prompts.data?.find((p) => p.id === promptId);

  const start = async () => {
    setRunning(true);
    try {
      const experiment = await runEvaluation(
        {
          name,
          dataset_id: datasetId,
          model_config_id: modelId,
          prompt_id: promptId,
          prompt_version: version,
          metrics,
        },
        setProgress,
      );
      toast.success("Evaluation complete");
      void navigate({
        to: "/experiments/$experimentId",
        params: { experimentId: experiment.id },
      });
    } catch (e) {
      toast.error((e as Error).message);
      setRunning(false);
      setProgress(null);
    }
  };

  if (loading) return <LoadingState variant="cards" rows={3} />;
  if (failed) return <ErrorState message="Could not load configuration options." />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="New Evaluation"
        description="Run a dataset against a model + prompt version and score it with the selected metrics."
      />

      <div className="grid gap-4 xl:grid-cols-[2fr_1fr]">
        <div className="panel space-y-4 p-5">
          <SectionHeader title="Run configuration" description="all fields required" />

          <div className="space-y-1.5">
            <Label htmlFor="ev-name">Experiment name</Label>
            <Input id="ev-name" value={name} onChange={(e) => setName(e.target.value)} />
          </div>

          <div className="grid gap-3 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label htmlFor="ev-dataset">Dataset</Label>
              <select
                id="ev-dataset"
                className="h-9 w-full rounded-sm border border-input bg-transparent px-3 text-sm"
                value={datasetId}
                onChange={(e) => setDatasetId(e.target.value)}
              >
                {datasets.data?.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="ev-model">Model configuration</Label>
              <select
                id="ev-model"
                className="h-9 w-full rounded-sm border border-input bg-transparent px-3 text-sm"
                value={modelId}
                onChange={(e) => setModelId(e.target.value)}
              >
                {models.data?.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="ev-prompt">Prompt configuration</Label>
              <select
                id="ev-prompt"
                className="h-9 w-full rounded-sm border border-input bg-transparent px-3 text-sm"
                value={promptId}
                onChange={(e) => {
                  setPromptId(e.target.value);
                  const p = prompts.data?.find((x) => x.id === e.target.value);
                  setVersion(p?.latest_version ?? 1);
                }}
              >
                {prompts.data?.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="ev-version">Prompt version</Label>
              <select
                id="ev-version"
                className="h-9 w-full rounded-sm border border-input bg-transparent px-3 text-sm"
                value={version}
                onChange={(e) => setVersion(Number(e.target.value))}
              >
                {prompt?.versions.map((v) => (
                  <option key={v.id} value={v.version}>
                    v{v.version} — {v.notes}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <Label>Evaluation metrics</Label>
            <div className="grid gap-2 sm:grid-cols-2">
              {METRIC_OPTIONS.map((m) => (
                <label
                  key={m.value}
                  className="flex cursor-pointer items-start gap-2.5 rounded-sm border border-border p-3"
                >
                  <Checkbox
                    checked={metrics.includes(m.value)}
                    onCheckedChange={(checked) =>
                      setMetrics((prev) =>
                        checked ? [...prev, m.value] : prev.filter((x) => x !== m.value),
                      )
                    }
                  />
                  <span>
                    <span className="block text-sm font-medium">{m.label}</span>
                    <span className="block text-xs text-muted-foreground">{m.hint}</span>
                  </span>
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="panel h-fit p-5">
          <SectionHeader title="Evaluation summary" description="review before running" />
          <div className="mt-3">
            <Row label="Dataset" value={dataset?.name ?? "—"} />
            <Row label="Number of cases" value={String(dataset?.case_count ?? 0)} />
            <Row label="Provider" value={model?.provider ?? "—"} />
            <Row label="Model" value={model?.model ?? "—"} />
            <Row label="Prompt version" value={`${prompt?.name ?? ""} v${version}`} />
            <Row label="Selected metrics" value={String(metrics.length)} />
          </div>

          {progress && (
            <div className="mt-4 space-y-2 rounded-sm border border-border bg-muted/40 p-3">
              <p className="text-sm font-medium">{progress.message}</p>
              <Progress value={(progress.completed / (progress.total || 1)) * 100} />
              <p className="num text-[11px] text-muted-foreground">stage: {progress.stage}</p>
            </div>
          )}

          <Button className="mt-4 w-full" onClick={() => void start()} disabled={running}>
            <Play className="size-4" />
            {running ? "Running evaluation…" : "Run Evaluation"}
          </Button>
        </div>
      </div>
    </div>
  );
}
