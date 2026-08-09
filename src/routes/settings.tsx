import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Check, CheckCircle2, ShieldCheck, Sliders, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { getSettings, updateEvaluationDefaults, updateRegressionThresholds } from "@/api/settings";
import { PageHeader, SectionHeader } from "@/components/common/PageHeader";
import { Pill } from "@/components/common/StatusBadge";
import { ErrorState, LoadingState } from "@/components/common/States";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

import { formatCategory } from "@/utils/format";
import type { EvaluationCategory, MetricKey } from "@/types";

export const Route = createFileRoute("/settings")({
  head: () => ({
    meta: [
      { title: "Settings — LLMOps Studio" },
      {
        name: "description",
        content: "Evaluation defaults, regression threshold rules, and LLM provider connectivity.",
      },
      { property: "og:title", content: "Settings — LLMOps Studio" },
      { property: "og:description", content: "Evaluation defaults and regression policies." },
    ],
  }),
  component: SettingsPage,
});

const ALL_METRICS: { key: MetricKey; label: string }[] = [
  { key: "semantic_similarity", label: "Semantic Similarity" },
  { key: "llm_judge", label: "LLM Judge" },
  { key: "response_completeness", label: "Response Completeness" },
  { key: "keyword_match", label: "Keyword Match" },
  { key: "exact_match", label: "Exact Match" },
];

const ALL_CATEGORIES: EvaluationCategory[] = [
  "factuality",
  "reasoning",
  "summarization",
  "customer-support",
  "instruction-following",
  "safety",
  "billing",
  "technical",
  "account-management",
  "general",
];

function SettingsPage() {
  const queryClient = useQueryClient();
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["settings"],
    queryFn: getSettings,
  });

  const [evalDefaults, setEvalDefaults] = useState({
    default_metrics: [] as MetricKey[],
    concurrency: 5,
    judge_model: "llama-3.3-70b-versatile",
  });

  const [thresholds, setThresholds] = useState({
    max_quality_regression_pct: 3.0,
    max_factuality_regression_pct: 2.0,
    max_latency_increase_pct: 15.0,
    max_cost_increase_pct: 20.0,
    critical_categories: [] as EvaluationCategory[],
  });

  useEffect(() => {
    if (data) {
      setEvalDefaults(data.evaluation_defaults);
      setThresholds(data.regression_thresholds);
    }
  }, [data]);

  const saveEvalDefaultsMutation = useMutation({
    mutationFn: updateEvaluationDefaults,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["settings"] });
      toast.success("Evaluation defaults saved successfully.");
    },
    onError: (err: Error) => {
      toast.error(`Failed to save evaluation defaults: ${err.message}`);
    },
  });

  const saveThresholdsMutation = useMutation({
    mutationFn: updateRegressionThresholds,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["settings"] });
      toast.success("Regression thresholds saved successfully.");
    },
    onError: (err: Error) => {
      toast.error(`Failed to save regression thresholds: ${err.message}`);
    },
  });

  if (isLoading) return <LoadingState rows={6} />;
  if (isError)
    return <ErrorState message={(error as Error).message} onRetry={() => void refetch()} />;
  if (!data) return null;

  const toggleMetric = (key: MetricKey) => {
    setEvalDefaults((prev) => ({
      ...prev,
      default_metrics: prev.default_metrics.includes(key)
        ? prev.default_metrics.filter((m) => m !== key)
        : [...prev.default_metrics, key],
    }));
  };

  const toggleCategory = (cat: EvaluationCategory) => {
    setThresholds((prev) => ({
      ...prev,
      critical_categories: prev.critical_categories.includes(cat)
        ? prev.critical_categories.filter((c) => c !== cat)
        : [...prev.critical_categories, cat],
    }));
  };

  return (
    <div className="space-y-6 max-w-5xl">
      <PageHeader
        title="Settings"
        description="Workspace configuration for evaluation defaults, regression testing thresholds, and connected model providers."
      />

      {/* Provider Connectivity Status */}
      <div className="panel p-5 space-y-4">
        <SectionHeader
          title="Provider Status"
          description="Status of configured LLM inference providers used for evaluations and judge runs."
        />
        <div className="grid gap-4 sm:grid-cols-2">
          {data.providers.map((p) => (
            <div
              key={p.provider}
              className="rounded-sm border border-border p-4 space-y-3 bg-background"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-base">{p.label}</span>
                  {p.configured ? (
                    <Pill tone="pass">
                      <span className="flex items-center gap-1">
                        <CheckCircle2 className="size-3" /> Connected
                      </span>
                    </Pill>
                  ) : (
                    <Pill tone="fail">
                      <span className="flex items-center gap-1">
                        <XCircle className="size-3" /> Not Configured
                      </span>
                    </Pill>
                  )}
                </div>
              </div>
              <div>
                <p className="text-xs font-semibold text-muted-foreground mb-1.5">
                  Available Models ({p.models.length})
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {p.models.map((m) => (
                    <span
                      key={m}
                      className="inline-flex items-center rounded bg-muted/60 px-2 py-0.5 text-xs font-mono"
                    >
                      {m}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Evaluation Defaults */}
      <div className="panel p-5 space-y-5">
        <div className="flex items-center justify-between border-b border-border pb-4">
          <SectionHeader
            title="Evaluation Defaults"
            description="Default parameters and judge models automatically pre-selected when launching new runs."
          />
          <Button
            size="sm"
            onClick={() => saveEvalDefaultsMutation.mutate(evalDefaults)}
            disabled={saveEvalDefaultsMutation.isPending}
          >
            {saveEvalDefaultsMutation.isPending ? "Saving..." : "Save Defaults"}
          </Button>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <div className="space-y-3">
            <label className="text-sm font-semibold">Default Evaluation Metrics</label>
            <div className="space-y-2">
              {ALL_METRICS.map((m) => {
                const checked = evalDefaults.default_metrics.includes(m.key);
                return (
                  <label
                    key={m.key}
                    className="flex items-center gap-2.5 rounded-sm border border-border p-2.5 text-sm cursor-pointer hover:bg-muted/40"
                  >
                    <input
                      type="checkbox"
                      checked={checked}
                      onChange={() => toggleMetric(m.key)}
                      className="size-4 rounded border-input text-primary focus:ring-primary"
                    />
                    <span>{m.label}</span>
                  </label>
                );
              })}
            </div>
          </div>

          <div className="space-y-4">
            <div className="space-y-1.5">
              <label htmlFor="judge-model-select" className="text-sm font-semibold">
                Default LLM Judge Model
              </label>
              <select
                id="judge-model-select"
                className="w-full h-9 rounded-sm border border-input bg-background px-3 text-sm"
                value={evalDefaults.judge_model}
                onChange={(e) =>
                  setEvalDefaults((prev) => ({ ...prev, judge_model: e.target.value }))
                }
              >
                <option value="llama-3.3-70b-versatile">Groq: llama-3.3-70b-versatile</option>
                <option value="llama-3.1-8b-instant">Groq: llama-3.1-8b-instant</option>
                <option value="gemini-3.6-flash">Gemini: gemini-3.6-flash</option>
                <option value="gemini-3.5-flash">Gemini: gemini-3.5-flash</option>
                <option value="gemini-3.5-flash-lite">Gemini: gemini-3.5-flash-lite</option>
              </select>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-sm">
                <label htmlFor="concurrency-range" className="font-semibold">
                  Evaluation Concurrency
                </label>
                <span className="num font-mono">{evalDefaults.concurrency} concurrent cases</span>
              </div>
              <input
                id="concurrency-range"
                type="range"
                min={1}
                max={10}
                value={evalDefaults.concurrency}
                onChange={(e) =>
                  setEvalDefaults((prev) => ({ ...prev, concurrency: Number(e.target.value) }))
                }
                className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary"
              />
              <p className="text-xs text-muted-foreground">
                Number of parallel model requests made during evaluation suite runs.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Regression Thresholds */}
      <div className="panel p-5 space-y-5">
        <div className="flex items-center justify-between border-b border-border pb-4">
          <SectionHeader
            title="Regression Policy & Thresholds"
            description="Tolerances and critical category rules that govern the Promotion Gate PASS/FAIL decision."
          />
          <Button
            size="sm"
            onClick={() => saveThresholdsMutation.mutate(thresholds)}
            disabled={saveThresholdsMutation.isPending}
          >
            {saveThresholdsMutation.isPending ? "Saving..." : "Save Thresholds"}
          </Button>
        </div>

        <div className="grid gap-4 sm:grid-cols-3">
          <div className="space-y-1.5">
            <label htmlFor="max-quality-reg" className="text-sm font-medium">
              Max Quality Regression (%)
            </label>
            <Input
              id="max-quality-reg"
              type="number"
              step="0.5"
              value={thresholds.max_quality_regression_pct}
              onChange={(e) =>
                setThresholds((prev) => ({
                  ...prev,
                  max_quality_regression_pct: Number(e.target.value),
                }))
              }
            />
            <p className="text-xs text-muted-foreground">
              Maximum allowable overall quality score drop before failing promotion.
            </p>
          </div>

          <div className="space-y-1.5">
            <label htmlFor="max-factuality-reg" className="text-sm font-medium">
              Max Factuality Regression (%)
            </label>
            <Input
              id="max-factuality-reg"
              type="number"
              step="0.5"
              value={thresholds.max_factuality_regression_pct}
              onChange={(e) =>
                setThresholds((prev) => ({
                  ...prev,
                  max_factuality_regression_pct: Number(e.target.value),
                }))
              }
            />
            <p className="text-xs text-muted-foreground">
              Maximum allowable drop on core factuality & reasoning dimensions.
            </p>
          </div>

          <div className="space-y-1.5">
            <label htmlFor="max-latency-inc" className="text-sm font-medium">
              Max Latency Increase (%)
            </label>
            <Input
              id="max-latency-inc"
              type="number"
              step="1"
              value={thresholds.max_latency_increase_pct}
              onChange={(e) =>
                setThresholds((prev) => ({
                  ...prev,
                  max_latency_increase_pct: Number(e.target.value),
                }))
              }
            />
            <p className="text-xs text-muted-foreground">
              Maximum allowable percentage increase in average response latency.
            </p>
          </div>
        </div>

        <div className="space-y-3 pt-2">
          <label className="text-sm font-semibold">Critical Categories (Zero Tolerance)</label>
          <p className="text-xs text-muted-foreground">
            Any regression (delta &lt; 0%) in a critical category triggers an immediate Promotion
            Gate BLOCKED status.
          </p>
          <div className="flex flex-wrap gap-2">
            {ALL_CATEGORIES.map((cat) => {
              const active = thresholds.critical_categories.includes(cat);
              return (
                <button
                  key={cat}
                  type="button"
                  onClick={() => toggleCategory(cat)}
                  className={`px-3 py-1.5 rounded-sm text-xs font-medium border transition-colors ${
                    active
                      ? "bg-destructive/10 border-destructive text-destructive"
                      : "bg-background border-border text-muted-foreground hover:bg-muted"
                  }`}
                >
                  {formatCategory(cat)} {active ? "✓ (Critical)" : ""}
                </button>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
