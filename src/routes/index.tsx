import { useQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { FlaskConical, Gauge, ShieldCheck, Timer } from "lucide-react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getDashboardSummary } from "@/api/experiments";
import { MetricCard } from "@/components/common/MetricCard";
import { PageHeader, SectionHeader } from "@/components/common/PageHeader";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/States";
import { StatusBadge } from "@/components/common/StatusBadge";
import { ExperimentTable } from "@/components/experiments/ExperimentTable";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatDateTime, formatLatency, formatPercent } from "@/utils/format";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Dashboard — LLMOps Studio" },
      {
        name: "description",
        content:
          "Evaluation health overview: quality, latency and regression pass rate across LLM experiments.",
      },
      { property: "og:title", content: "Dashboard — LLMOps Studio" },
      {
        property: "og:description",
        content: "Quality, latency and regression status across your LLM experiments.",
      },
    ],
  }),
  component: DashboardPage,
});

const axis = {
  stroke: "var(--color-muted-foreground)",
  fontSize: 11,
  tickLine: false,
  axisLine: false,
};

function ChartCard({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: React.ReactNode;
}) {
  return (
    <div className="panel p-4">
      <SectionHeader title={title} description={subtitle} />
      <div className="mt-4 h-[200px]">
        <ResponsiveContainer width="100%" height="100%">
          {children as React.ReactElement}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

const tooltipStyle = {
  contentStyle: {
    background: "var(--color-popover)",
    border: "1px solid var(--color-border)",
    borderRadius: "6px",
    fontSize: "12px",
    color: "var(--color-popover-foreground)",
  },
  labelStyle: { color: "var(--color-muted-foreground)" },
};

function DashboardPage() {
  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["dashboard"],
    queryFn: getDashboardSummary,
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Evaluation Overview"
        description="Quality, latency and regression health across LLM experiments."
        actions={
          <>
            <Button asChild variant="outline" size="sm">
              <Link to="/regression">Open regression check</Link>
            </Button>
            <Button asChild size="sm">
              <Link to="/evaluations/new">New evaluation</Link>
            </Button>
          </>
        }
      />

      {isLoading && <LoadingState variant="cards" rows={6} />}
      {isError && <ErrorState message={(error as Error).message} onRetry={() => void refetch()} />}

      {data && (
        <>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <MetricCard
              label="Evaluation Runs"
              value={String(data.total_experiments)}
              hint="all time"
              icon={FlaskConical}
            />
            <MetricCard
              label="Avg Quality"
              value={formatPercent(data.avg_quality_score)}
              icon={Gauge}
            />
            <MetricCard
              label="Avg Latency"
              value={formatLatency(data.avg_latency_ms)}
              icon={Timer}
            />
            <MetricCard
              label="Regression Pass Rate"
              value={formatPercent(data.regression_pass_rate)}
              icon={ShieldCheck}
            />
          </div>

          <div className="grid gap-3 lg:grid-cols-2">
            <ChartCard title="Quality Score Over Time" subtitle="overall score per run">
              <AreaChart data={data.quality_over_time}>
                <defs>
                  <linearGradient id="q" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="var(--color-chart-1)" stopOpacity={0.35} />
                    <stop offset="100%" stopColor="var(--color-chart-1)" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="var(--color-border)" vertical={false} />
                <XAxis dataKey="date" {...axis} />
                <YAxis domain={[70, 100]} width={34} {...axis} />
                <Tooltip {...tooltipStyle} />
                <Area
                  type="monotone"
                  dataKey="score"
                  stroke="var(--color-chart-1)"
                  strokeWidth={2}
                  fill="url(#q)"
                />
              </AreaChart>
            </ChartCard>

            <ChartCard title="Average Latency Over Time" subtitle="milliseconds per run">
              <LineChart data={data.latency_over_time}>
                <CartesianGrid stroke="var(--color-border)" vertical={false} />
                <XAxis dataKey="date" {...axis} />
                <YAxis width={42} {...axis} />
                <Tooltip {...tooltipStyle} />
                <Line
                  type="monotone"
                  dataKey="latency"
                  stroke="var(--color-chart-3)"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ChartCard>
          </div>

          <div className="panel">
            <div className="border-b border-border p-4">
              <SectionHeader
                title="Recent Experiments"
                description="latest evaluation runs"
                actions={
                  <Button asChild variant="ghost" size="sm">
                    <Link to="/experiments">View all</Link>
                  </Button>
                }
              />
            </div>
            {data.recent_experiments.length === 0 ? (
              <EmptyState title="No experiments yet" className="m-4" />
            ) : (
              <ExperimentTable experiments={data.recent_experiments} compact />
            )}
          </div>

          <div className="panel">
            <div className="border-b border-border p-4">
              <SectionHeader
                title="Recent Regression Activity"
                description="threshold breaches and warnings"
                actions={
                  <Button asChild variant="ghost" size="sm">
                    <Link to="/regression">View all</Link>
                  </Button>
                }
              />
            </div>
            {data.alerts.length === 0 ? (
              <div className="p-6 text-center text-sm text-muted-foreground">
                No recent regression alerts
              </div>
            ) : (
              <div className="overflow-x-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent">
                      <TableHead className="w-28">Status</TableHead>
                      <TableHead>Experiment</TableHead>
                      <TableHead>Alert</TableHead>
                      <TableHead className="text-right">Created</TableHead>
                      <TableHead className="text-right">Action</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.alerts.slice(0, 5).map((a) => (
                      <TableRow key={a.id}>
                        <TableCell>
                          <StatusBadge status={a.severity} />
                        </TableCell>
                        <TableCell className="font-medium text-sm">
                          <Link
                            to="/experiments/$experimentId"
                            params={{ experimentId: a.experiment_id }}
                            className="hover:text-primary hover:underline"
                          >
                            {a.experiment_id}
                          </Link>
                        </TableCell>
                        <TableCell className="text-sm">{a.message}</TableCell>
                        <TableCell className="num text-right text-xs text-muted-foreground">
                          {formatDateTime(a.created_at)}
                        </TableCell>
                        <TableCell className="text-right">
                          <Button asChild variant="ghost" size="sm">
                            <Link
                              to="/experiments/$experimentId"
                              params={{ experimentId: a.experiment_id }}
                            >
                              View
                            </Link>
                          </Button>
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
    </div>
  );
}
