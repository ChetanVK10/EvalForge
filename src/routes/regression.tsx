import { useQuery } from "@tanstack/react-query";
import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { ArrowLeftRight, CheckCircle2, ShieldAlert, ShieldCheck, XCircle } from "lucide-react";
import { useState } from "react";
import { compareExperiments } from "@/api/regressions";
import { listExperiments } from "@/api/experiments";
import { MetricCard } from "@/components/common/MetricCard";
import { PageHeader, SectionHeader } from "@/components/common/PageHeader";
import { Pill, StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/States";
import { MetricComparisonTable } from "@/components/regression/MetricComparisonTable";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import {
  formatCategory,
  formatDelta,
  formatLatency,
  formatPercent,
  truncate,
} from "@/utils/format";
import type { CategoryRegression, RegressionCase } from "@/types";

interface RegressionSearch {
  baseline?: string | undefined;
  candidate?: string | undefined;
}

export const Route = createFileRoute("/regression")({
  validateSearch: (search: Record<string, unknown>): RegressionSearch => {
    const b = search["baseline"];
    const c = search["candidate"];
    return {
      baseline: typeof b === "string" && b ? b : undefined,
      candidate: typeof c === "string" && c ? c : undefined,
    };
  },
  head: () => ({
    meta: [
      { title: "Regression Comparison — LLMOps Studio" },
      {
        name: "description",
        content: "Compare candidate model/prompt against baseline with automated promotion gates.",
      },
      { property: "og:title", content: "Regression Comparison — LLMOps Studio" },
      { property: "og:description", content: "Automated regression testing and promotion gates." },
    ],
  }),
  component: RegressionPage,
});

function RegressionPage() {
  const { baseline: searchBaseline, candidate: searchCandidate } = Route.useSearch();
  const navigate = useNavigate();

  const [inspectCase, setInspectCase] = useState<RegressionCase | null>(null);

  const { data: experiments = [], isLoading: loadingExperiments } = useQuery({
    queryKey: ["experiments"],
    queryFn: () => listExperiments(),
  });

  // Prefer completed experiments for regression comparison
  const completedExperiments = experiments.filter((e) => e.status === "completed");
  const availableExperiments = completedExperiments.length > 0 ? completedExperiments : experiments;

  // Determine initial baseline selection
  const isSearchBaselineValid = Boolean(
    searchBaseline && availableExperiments.some((e) => e.id === searchBaseline),
  );
  const baselineId = isSearchBaselineValid
    ? (searchBaseline as string)
    : (availableExperiments[0]?.id ?? "");

  const baselineExp = availableExperiments.find((e) => e.id === baselineId);
  const validCandidates = availableExperiments.filter(
    (e) => e.id !== baselineId && (!baselineExp || e.dataset_id === baselineExp.dataset_id),
  );

  // Determine initial candidate selection
  const isSearchCandidateValid = Boolean(
    searchCandidate && validCandidates.some((e) => e.id === searchCandidate),
  );
  const candidateId = isSearchCandidateValid
    ? (searchCandidate as string)
    : (validCandidates[0]?.id ?? "");

  const canCompare = Boolean(baselineId && candidateId && baselineId !== candidateId);

  const {
    data: comparison,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: ["regression-comparison", baselineId, candidateId],
    queryFn: () =>
      compareExperiments({
        baseline_experiment_id: baselineId,
        candidate_experiment_id: candidateId,
      }),
    enabled: canCompare,
  });

  const setBaseline = (newBaseline: string) => {
    const newCand =
      newBaseline === candidateId
        ? (availableExperiments.find((e) => e.id !== newBaseline)?.id ?? "")
        : candidateId;

    void navigate({
      to: "/regression",
      search: { baseline: newBaseline || undefined, candidate: newCand || undefined },
    });
  };

  const setCandidate = (newCandidate: string) => {
    void navigate({
      to: "/regression",
      search: { baseline: baselineId || undefined, candidate: newCandidate || undefined },
    });
  };

  const swap = () => {
    if (!baselineId || !candidateId) return;
    void navigate({
      to: "/regression",
      search: { baseline: candidateId, candidate: baselineId },
    });
  };

  const selectCls =
    "h-9 rounded-sm border border-input bg-background px-3 pr-8 text-sm font-medium max-w-full min-w-0 truncate cursor-pointer";

  return (
    <div className="space-y-6">
      <PageHeader
        title="Regression Comparison"
        description="Automated baseline vs candidate evaluation comparison with metric delta thresholds and promotion gates."
      />

      <div className="panel flex flex-wrap items-center justify-between gap-4 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex flex-col gap-1 min-w-0 max-w-xs sm:max-w-sm">
            <label
              htmlFor="baseline-select"
              className="text-xs font-semibold text-muted-foreground"
            >
              Baseline Experiment
            </label>
            <select
              id="baseline-select"
              className={selectCls}
              value={baselineId}
              onChange={(e) => setBaseline(e.target.value)}
              disabled={loadingExperiments || availableExperiments.length === 0}
              aria-label="Baseline experiment"
            >
              {availableExperiments.length === 0 ? (
                <option value="">No experiments available</option>
              ) : (
                availableExperiments.map((exp) => (
                  <option
                    key={exp.id}
                    value={exp.id}
                    title={`${exp.name} (${exp.prompt_name} v${exp.prompt_version})`}
                  >
                    {exp.name} ({exp.prompt_name} v{exp.prompt_version})
                  </option>
                ))
              )}
            </select>
          </div>

          <Button
            variant="ghost"
            size="icon"
            onClick={swap}
            disabled={!canCompare}
            className="mt-4"
            title="Swap baseline and candidate"
            aria-label="Swap baseline and candidate"
          >
            <ArrowLeftRight className="size-4" />
          </Button>

          <div className="flex flex-col gap-1 min-w-0 max-w-xs sm:max-w-sm">
            <label
              htmlFor="candidate-select"
              className="text-xs font-semibold text-muted-foreground"
            >
              Candidate Experiment
            </label>
            <select
              id="candidate-select"
              className={selectCls}
              value={candidateId}
              onChange={(e) => setCandidate(e.target.value)}
              disabled={loadingExperiments || validCandidates.length === 0}
              aria-label="Candidate experiment"
            >
              {validCandidates.length === 0 ? (
                <option value="">No candidate available</option>
              ) : (
                validCandidates.map((exp) => (
                  <option
                    key={exp.id}
                    value={exp.id}
                    title={`${exp.name} (${exp.prompt_name} v${exp.prompt_version})`}
                  >
                    {exp.name} ({exp.prompt_name} v{exp.prompt_version})
                  </option>
                ))
              )}
            </select>
          </div>
        </div>

        {comparison && (
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-xs text-muted-foreground">Dataset</p>
              <p className="text-sm font-semibold">{comparison.baseline.dataset_name}</p>
            </div>
            <div className="h-8 w-px bg-border" />
            <div className="text-right">
              <p className="text-xs text-muted-foreground">Baseline Model</p>
              <p className="text-sm font-medium">{comparison.baseline.model}</p>
            </div>
            <div className="h-8 w-px bg-border" />
            <div className="text-right">
              <p className="text-xs text-muted-foreground">Candidate Model</p>
              <p className="text-sm font-medium">{comparison.candidate.model}</p>
            </div>
          </div>
        )}
      </div>

      {loadingExperiments ? (
        <LoadingState rows={8} />
      ) : availableExperiments.length < 2 ? (
        <EmptyState
          title="No comparison available yet"
          message="Run at least two completed experiments on the same dataset to compare baseline and candidate performance."
        />
      ) : !canCompare ? (
        <EmptyState
          title="Select baseline and candidate experiments"
          message="Choose two distinct experiments from the dropdowns above to trigger automated regression testing and promotion gate evaluation."
        />
      ) : (
        <>
          {isLoading && <LoadingState rows={8} />}
          {isError && (
            <ErrorState message={(error as Error).message} onRetry={() => void refetch()} />
          )}

          {comparison && (
            <>
              {/* Verdict Banner */}
              <div
                className={cn(
                  "panel flex flex-col gap-4 border-l-4 p-5 sm:flex-row sm:items-center sm:justify-between",
                  comparison.verdict === "FAIL"
                    ? "border-l-destructive bg-destructive/5"
                    : comparison.verdict === "WARNING"
                      ? "border-l-warning bg-warning/5"
                      : "border-l-success bg-success/5",
                )}
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    {comparison.verdict === "FAIL" ? (
                      <XCircle className="size-6 text-destructive" />
                    ) : comparison.verdict === "WARNING" ? (
                      <ShieldAlert className="size-6 text-warning" />
                    ) : (
                      <CheckCircle2 className="size-6 text-success" />
                    )}
                    <h2 className="text-xl font-bold tracking-tight">
                      Regression Verdict: {comparison.verdict}
                    </h2>
                  </div>
                  <p className="text-sm text-muted-foreground">{comparison.summary}</p>
                </div>

                <div className="flex items-center gap-3">
                  <div
                    className={cn(
                      "flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-semibold border",
                      comparison.promotion_gate.passed
                        ? "border-success/30 bg-success/10 text-success"
                        : "border-destructive/30 bg-destructive/10 text-destructive",
                    )}
                  >
                    {comparison.promotion_gate.passed ? (
                      <>
                        <ShieldCheck className="size-4" />
                        PROMOTION GATE: PASSED
                      </>
                    ) : (
                      <>
                        <ShieldAlert className="size-4" />
                        PROMOTION GATE: BLOCKED
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Quick Metrics Summary Cards */}
              <div className="grid gap-3 sm:grid-cols-3">
                <MetricCard
                  label="Overall Quality Delta"
                  value={formatDelta(
                    comparison.candidate.quality_score != null &&
                      comparison.baseline.quality_score != null
                      ? comparison.candidate.quality_score - comparison.baseline.quality_score
                      : null,
                  )}
                  hint={`Baseline: ${formatPercent(comparison.baseline.quality_score)} → Candidate: ${formatPercent(comparison.candidate.quality_score)}`}
                />
                <MetricCard
                  label="Pass Rate Delta"
                  value={formatDelta(
                    comparison.candidate.pass_rate != null && comparison.baseline.pass_rate != null
                      ? comparison.candidate.pass_rate - comparison.baseline.pass_rate
                      : null,
                  )}
                  hint={`Baseline: ${formatPercent(comparison.baseline.pass_rate)} → Candidate: ${formatPercent(comparison.candidate.pass_rate)}`}
                />
                <MetricCard
                  label="Latency Delta"
                  value={formatDelta(
                    comparison.candidate.avg_latency_ms != null &&
                      comparison.baseline.avg_latency_ms != null &&
                      comparison.baseline.avg_latency_ms !== 0
                      ? ((comparison.candidate.avg_latency_ms -
                          comparison.baseline.avg_latency_ms) /
                          comparison.baseline.avg_latency_ms) *
                          100
                      : null,
                  )}
                  hint={`Baseline: ${formatLatency(comparison.baseline.avg_latency_ms)} → Candidate: ${formatLatency(comparison.candidate.avg_latency_ms)}`}
                />
              </div>

              {/* Promotion Gate Breakdown & Reasons */}
              <div className="panel p-5 space-y-4">
                <SectionHeader
                  title="Promotion Gate Rules"
                  description="Configured deployment policies required for automated candidate promotion."
                />

                <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
                  {comparison.promotion_gate.rules.map((rule) => (
                    <div
                      key={rule.label}
                      className={cn(
                        "flex items-center justify-between rounded-sm border p-3 text-sm",
                        rule.passed
                          ? "border-border bg-background"
                          : "border-destructive/30 bg-destructive/5",
                      )}
                    >
                      <div>
                        <p className="font-medium">{rule.label}</p>
                        <p className="text-xs text-muted-foreground">Limit: {rule.limit}</p>
                      </div>
                      <div className="text-right">
                        <p
                          className={cn(
                            "num font-semibold",
                            rule.passed ? "text-success" : "text-destructive",
                          )}
                        >
                          {rule.actual}
                        </p>
                        <span
                          className={cn(
                            "text-[10px] uppercase font-bold",
                            rule.passed ? "text-success" : "text-destructive",
                          )}
                        >
                          {rule.passed ? "PASS" : "FAIL"}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Failure Explanations */}
                {!comparison.promotion_gate.passed &&
                  comparison.promotion_gate.reasons.length > 0 && (
                    <div className="rounded-sm border border-destructive/30 bg-destructive/10 p-4 space-y-2">
                      <p className="text-sm font-semibold text-destructive flex items-center gap-1.5">
                        <ShieldAlert className="size-4" /> Deterministic Promotion Failure Reasons:
                      </p>
                      <ul className="list-disc list-inside space-y-1 text-xs text-destructive/90">
                        {comparison.promotion_gate.reasons.map((reason, idx) => (
                          <li key={idx}>{reason}</li>
                        ))}
                      </ul>
                    </div>
                  )}
              </div>

              {/* Metric Comparison Table */}
              <div className="panel p-4">
                <SectionHeader
                  title="Metric Comparison"
                  description="Detailed score comparison across quality and latency dimensions against configured thresholds."
                />
                <div className="mt-4">
                  <MetricComparisonTable metrics={comparison.metrics} />
                </div>
              </div>

              {/* Category Performance Comparison */}
              <div className="panel p-4 space-y-4">
                <SectionHeader
                  title="Category Regression Breakdown"
                  description="Score performance by dataset evaluation category."
                />
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="hover:bg-transparent">
                        <TableHead>Category</TableHead>
                        <TableHead>Critical Category</TableHead>
                        <TableHead className="text-right">Baseline Score</TableHead>
                        <TableHead className="text-right">Candidate Score</TableHead>
                        <TableHead className="text-right">Delta</TableHead>
                        <TableHead className="text-right">Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {comparison.categories.map((cat: CategoryRegression) => {
                        const isRegressed = cat.delta_pct < 0;
                        return (
                          <TableRow key={cat.category}>
                            <TableCell className="font-medium text-sm">
                              {formatCategory(cat.category)}
                            </TableCell>
                            <TableCell>
                              {cat.critical ? (
                                <Pill tone="fail">CRITICAL</Pill>
                              ) : (
                                <Pill tone="neutral">Standard</Pill>
                              )}
                            </TableCell>
                            <TableCell className="num text-right text-sm">
                              {formatPercent(cat.baseline)}
                            </TableCell>
                            <TableCell className="num text-right text-sm font-medium">
                              {formatPercent(cat.candidate)}
                            </TableCell>
                            <TableCell
                              className={cn(
                                "num text-right text-sm font-semibold",
                                cat.delta_pct === 0
                                  ? "text-muted-foreground"
                                  : isRegressed
                                    ? "text-destructive"
                                    : "text-success",
                              )}
                            >
                              {formatDelta(cat.delta_pct)}
                            </TableCell>
                            <TableCell className="text-right">
                              <StatusBadge
                                status={
                                  isRegressed && cat.critical
                                    ? "FAIL"
                                    : isRegressed
                                      ? "WARNING"
                                      : "PASS"
                                }
                                dot={false}
                              />
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              </div>

              {/* Regressed Cases Table */}
              <div className="panel">
                <div className="border-b border-border p-4">
                  <SectionHeader
                    title={`Regressed Cases (${comparison.regressed_cases.length})`}
                    description="Evaluation cases that passed in baseline but fail in candidate. Click any row to inspect side-by-side."
                  />
                </div>
                {comparison.regressed_cases.length === 0 ? (
                  <div className="p-4 text-sm text-muted-foreground flex items-center gap-2">
                    <CheckCircle2 className="size-4 text-success" />✓ No regressions detected.
                  </div>
                ) : (
                  <div className="max-h-[400px] overflow-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="hover:bg-transparent">
                          <TableHead>Category</TableHead>
                          <TableHead>Input Prompt</TableHead>
                          <TableHead className="text-right">Baseline Score</TableHead>
                          <TableHead className="text-right">Candidate Score</TableHead>
                          <TableHead className="text-right">Delta</TableHead>
                          <TableHead>Failure Reason</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {comparison.regressed_cases.map((c) => (
                          <TableRow
                            key={c.case_id}
                            className="cursor-pointer hover:bg-muted/50"
                            onClick={() => setInspectCase(c)}
                            tabIndex={0}
                            onKeyDown={(e) => e.key === "Enter" && setInspectCase(c)}
                          >
                            <TableCell className="text-xs">
                              <Pill tone="fail">{formatCategory(c.category)}</Pill>
                            </TableCell>
                            <TableCell className="max-w-[280px] text-sm">
                              {truncate(c.input, 90)}
                            </TableCell>
                            <TableCell className="num text-right text-sm font-medium text-success">
                              {formatPercent(c.baseline_score)}
                            </TableCell>
                            <TableCell className="num text-right text-sm font-medium text-destructive">
                              {formatPercent(c.candidate_score)}
                            </TableCell>
                            <TableCell className="num text-right text-sm font-semibold text-destructive">
                              {formatDelta(c.delta)}
                            </TableCell>
                            <TableCell className="max-w-[240px] text-xs text-destructive truncate">
                              {c.failure_reason}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </div>

              {/* Improved Cases Table */}
              <div className="panel">
                <div className="border-b border-border p-4">
                  <SectionHeader
                    title={`Improved Cases (${comparison.improved_cases.length})`}
                    description="Evaluation cases showing significant score gains. Click any row to inspect side-by-side."
                  />
                </div>
                {comparison.improved_cases.length === 0 ? (
                  <div className="p-4 text-sm text-muted-foreground">
                    No significant case-level improvements.
                  </div>
                ) : (
                  <div className="max-h-[300px] overflow-auto">
                    <Table>
                      <TableHeader>
                        <TableRow className="hover:bg-transparent">
                          <TableHead>Category</TableHead>
                          <TableHead>Input Prompt</TableHead>
                          <TableHead className="text-right">Baseline Score</TableHead>
                          <TableHead className="text-right">Candidate Score</TableHead>
                          <TableHead className="text-right">Delta</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {comparison.improved_cases.map((c) => (
                          <TableRow
                            key={c.case_id}
                            className="cursor-pointer hover:bg-muted/50"
                            onClick={() => setInspectCase(c)}
                            tabIndex={0}
                            onKeyDown={(e) => e.key === "Enter" && setInspectCase(c)}
                          >
                            <TableCell className="text-xs font-medium">
                              {formatCategory(c.category)}
                            </TableCell>
                            <TableCell className="max-w-[320px] text-sm">
                              {truncate(c.input, 90)}
                            </TableCell>
                            <TableCell className="num text-right text-sm text-muted-foreground">
                              {formatPercent(c.baseline_score)}
                            </TableCell>
                            <TableCell className="num text-right text-sm font-medium text-success">
                              {formatPercent(c.candidate_score)}
                            </TableCell>
                            <TableCell className="num text-right text-sm font-semibold text-success">
                              {formatDelta(c.delta)}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </div>
            </>
          )}
        </>
      )}

      {/* Side-by-side Case Inspection Modal */}
      <Dialog open={inspectCase !== null} onOpenChange={(o) => !o && setInspectCase(null)}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between gap-2 pr-6">
              <span>Case Side-by-Side Inspection</span>
              {inspectCase && (
                <Pill tone={inspectCase.delta < 0 ? "fail" : "pass"}>
                  Delta: {formatDelta(inspectCase.delta)}
                </Pill>
              )}
            </DialogTitle>
            <DialogDescription>
              Case ID: {inspectCase?.case_id} · Category:{" "}
              {formatCategory(inspectCase?.category ?? "general")}
            </DialogDescription>
          </DialogHeader>

          {inspectCase && (
            <div className="space-y-4 text-sm mt-2">
              <div className="rounded-sm border border-border p-3 space-y-1 bg-muted/20">
                <p className="text-xs font-semibold text-muted-foreground uppercase">
                  Input Prompt
                </p>
                <p className="whitespace-pre-wrap">{inspectCase.input}</p>
              </div>

              <div className="rounded-sm border border-border p-3 space-y-1 bg-muted/20">
                <p className="text-xs font-semibold text-muted-foreground uppercase">
                  Expected Ground Truth
                </p>
                <p className="whitespace-pre-wrap text-muted-foreground">
                  {inspectCase.expected_output}
                </p>
              </div>

              <div className="grid gap-4 md:grid-cols-2">
                {/* Baseline Output */}
                <div className="panel p-4 space-y-2 border-l-4 border-l-info">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold text-muted-foreground">
                      Baseline Output ({comparison?.baseline.name})
                    </p>
                    <span className="num font-semibold text-sm">
                      Score: {formatPercent(inspectCase.baseline_score)}
                    </span>
                  </div>
                  <div className="rounded border border-border p-2.5 bg-background font-mono text-xs whitespace-pre-wrap min-h-[120px]">
                    {inspectCase.baseline_output}
                  </div>
                </div>

                {/* Candidate Output */}
                <div
                  className={cn(
                    "panel p-4 space-y-2 border-l-4",
                    inspectCase.delta < 0 ? "border-l-destructive" : "border-l-success",
                  )}
                >
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-semibold text-muted-foreground">
                      Candidate Output ({comparison?.candidate.name})
                    </p>
                    <span
                      className={cn(
                        "num font-semibold text-sm",
                        inspectCase.delta < 0 ? "text-destructive" : "text-success",
                      )}
                    >
                      Score: {formatPercent(inspectCase.candidate_score)}
                    </span>
                  </div>
                  <div className="rounded border border-border p-2.5 bg-background font-mono text-xs whitespace-pre-wrap min-h-[120px]">
                    {inspectCase.candidate_output}
                  </div>
                </div>
              </div>

              {inspectCase.failure_reason && (
                <div className="rounded-sm border border-destructive/30 bg-destructive/10 p-3 space-y-1">
                  <p className="text-xs font-semibold text-destructive">Failure Reason</p>
                  <p className="text-xs text-destructive">{inspectCase.failure_reason}</p>
                </div>
              )}

              {inspectCase.judge_explanation && (
                <div className="rounded-sm border border-border p-3 space-y-1 bg-muted/30">
                  <p className="text-xs font-semibold text-muted-foreground">
                    LLM Judge Explanation
                  </p>
                  <p className="text-xs text-muted-foreground whitespace-pre-wrap">
                    {inspectCase.judge_explanation}
                  </p>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
