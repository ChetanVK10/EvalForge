import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { toast } from "sonner";
import { Trash2 } from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { deleteExperiment, getExperimentResult } from "@/api/experiments";
import { DeleteConfirmDialog } from "@/components/common/DeleteConfirmDialog";
import { MetricCard } from "@/components/common/MetricCard";
import { PageHeader, SectionHeader } from "@/components/common/PageHeader";
import { ProviderBadge } from "@/components/common/ProviderBadge";
import { Pill, RunStatusBadge, StatusBadge } from "@/components/common/StatusBadge";
import { ErrorState, LoadingState } from "@/components/common/States";
import { CaseDetailDrawer } from "@/components/experiments/CaseDetailDrawer";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  formatCategory,
  formatDateTime,
  formatLatency,
  formatPercent,
  formatTokens,
  truncate,
} from "@/utils/format";
import type { EvaluationCaseResult } from "@/types";

export const Route = createFileRoute("/experiments/$experimentId")({
  head: () => ({
    meta: [
      { title: "Experiment Results — LLMOps Studio" },
      {
        name: "description",
        content: "Per-case scores, metric breakdown and failure inspection for an evaluation run.",
      },
      { property: "og:title", content: "Experiment Results — LLMOps Studio" },
      { property: "og:description", content: "Metric breakdown and failure inspection." },
    ],
  }),
  component: ExperimentResultsPage,
});

const axis = {
  stroke: "var(--color-muted-foreground)",
  fontSize: 11,
  tickLine: false,
  axisLine: false,
};

function ExperimentResultsPage() {
  const { experimentId } = Route.useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [active, setActive] = useState<EvaluationCaseResult | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["experiment-result", experimentId],
    queryFn: () => getExperimentResult(experimentId),
  });

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await deleteExperiment(experimentId);
      toast.success("Experiment deleted successfully.");
      void queryClient.invalidateQueries({ queryKey: ["experiments"] });
      void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      void navigate({ to: "/experiments" });
    } catch (err: any) {
      toast.error(err.message || "Failed to delete experiment.");
    } finally {
      setIsDeleting(false);
      setShowDeleteDialog(false);
    }
  };

  if (isLoading) return <LoadingState variant="cards" rows={6} />;
  if (isError)
    return <ErrorState message={(error as Error).message} onRetry={() => void refetch()} />;
  if (!data) return null;

  const e = data.experiment;

  return (
    <div className="space-y-6">
      <PageHeader
        title={e.name}
        description={`${e.dataset_name} · ${e.prompt_name} v${e.prompt_version}`}
        actions={
          <div className="flex items-center gap-2">
            <Button asChild variant="outline" size="sm">
              <Link to="/regression" search={{ candidate: e.id }}>
                Compare for regressions
              </Link>
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="text-destructive hover:bg-destructive/10 hover:text-destructive"
              onClick={() => setShowDeleteDialog(true)}
            >
              <Trash2 className="mr-1.5 size-3.5" />
              Delete
            </Button>
          </div>
        }
      />

      <div className="panel flex flex-wrap items-center gap-x-6 gap-y-2 p-4 text-sm">
        <span className="num text-xs text-muted-foreground">{e.id}</span>
        <span className="num text-xs text-muted-foreground">{formatDateTime(e.created_at)}</span>
        <ProviderBadge provider={e.provider} />
        <span className="num text-xs">{e.model}</span>
        <span className="text-xs text-muted-foreground">Prompt: <span className="font-medium text-foreground">{e.prompt_name}</span></span>
        <Pill tone="info">v{e.prompt_version}</Pill>
        <RunStatusBadge status={e.status} />
        <StatusBadge status={e.result_status || e.regression_status} />
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        <MetricCard label="Overall Quality" value={formatPercent(e.quality_score)} />
        <MetricCard label="Pass Rate" value={formatPercent(e.pass_rate)} />
        <MetricCard label="Avg Latency" value={formatLatency(e.avg_latency_ms)} />
        <MetricCard label="P95 Latency" value={formatLatency(e.p95_latency_ms)} />
        <MetricCard label="Total Tokens" value={formatTokens(e.total_tokens)} />
      </div>

      <div className="grid gap-3 xl:grid-cols-2">
        <div className="panel p-4">
          <SectionHeader title="Metric Breakdown" description="score per evaluation dimension" />
          <div className="mt-4 h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.metric_breakdown} layout="vertical" barSize={16}>
                <CartesianGrid stroke="var(--color-border)" horizontal={false} />
                <XAxis type="number" domain={[0, 100]} {...axis} />
                <YAxis type="category" dataKey="label" width={130} {...axis} />
                <Tooltip
                  contentStyle={{
                    background: "var(--color-popover)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "6px",
                    fontSize: "12px",
                  }}
                />
                <Bar dataKey="score" radius={[0, 3, 3, 0]} fill="var(--color-chart-1)" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="panel p-4">
          <SectionHeader title="Category Performance" description="score per case category" />
          <div className="mt-4 h-[220px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data.category_performance} barSize={30}>
                <CartesianGrid stroke="var(--color-border)" vertical={false} />
                <XAxis dataKey="label" {...axis} />
                <YAxis domain={[0, 100]} width={34} {...axis} />
                <Tooltip
                  contentStyle={{
                    background: "var(--color-popover)",
                    border: "1px solid var(--color-border)",
                    borderRadius: "6px",
                    fontSize: "12px",
                  }}
                />
                <Bar dataKey="score" radius={[3, 3, 0, 0]}>
                  {data.category_performance.map((c) => (
                    <Cell
                      key={c.key}
                      fill={
                        c.score == null
                          ? "var(--color-border)"
                          : c.score >= 90
                            ? "var(--color-chart-2)"
                            : c.score >= 85
                              ? "var(--color-chart-1)"
                              : "var(--color-chart-4)"
                      }
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="border-b border-border p-4">
          <SectionHeader
            title="Evaluation cases"
            description={`${data.cases.length} cases · click a row to inspect the failure`}
          />
        </div>
        <div className="max-h-[600px] overflow-auto">
          <Table>
            <TableHeader>
              <TableRow className="hover:bg-transparent">
                <TableHead>Input</TableHead>
                <TableHead>Expected Output</TableHead>
                <TableHead>Model Output</TableHead>
                <TableHead className="text-right">Score</TableHead>
                <TableHead className="text-right">Latency</TableHead>
                <TableHead className="text-right">Tokens</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.cases.map((c) => (
                <TableRow
                  key={c.id}
                  className="cursor-pointer"
                  onClick={() => setActive(c)}
                  tabIndex={0}
                  onKeyDown={(ev) => ev.key === "Enter" && setActive(c)}
                >
                  <TableCell className="max-w-[240px] text-sm">
                    {truncate(c.input, 80)}
                    <span className="mt-1 block text-[11px] text-muted-foreground">
                      {formatCategory(c.category)}
                    </span>
                  </TableCell>
                  <TableCell className="max-w-[240px] text-sm text-muted-foreground">
                    {truncate(c.expected_output, 80)}
                  </TableCell>
                  <TableCell className="max-w-[260px] text-sm text-muted-foreground">
                    {truncate(c.model_output, 90)}
                  </TableCell>
                  <TableCell className="num text-right text-sm font-medium">
                    {formatPercent(c.score)}
                  </TableCell>
                  <TableCell className="num text-right text-sm">
                    {formatLatency(c.latency_ms)}
                  </TableCell>
                  <TableCell className="num text-right text-sm">{formatTokens(c.tokens)}</TableCell>
                  <TableCell>
                    <div className="flex items-center gap-1.5">
                      <StatusBadge status={c.status} />
                      {c.execution_status === "failed" && <Pill tone="fail">Error</Pill>}
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>

      <CaseDetailDrawer
        caseResult={active}
        open={active !== null}
        onOpenChange={(o) => !o && setActive(null)}
      />

      <DeleteConfirmDialog
        open={showDeleteDialog}
        onOpenChange={setShowDeleteDialog}
        title={`Delete experiment "${e.name}"?`}
        description="This permanently removes this experiment and its evaluation results. This action cannot be undone."
        onConfirm={handleDelete}
        isDeleting={isDeleting}
      />
    </div>
  );
}
