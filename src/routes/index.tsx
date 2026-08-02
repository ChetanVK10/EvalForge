import { useQuery } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Activity, CircleDollarSign, FlaskConical, Gauge, ShieldCheck, Timer } from "lucide-react";
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
import { formatCost, formatDateTime, formatLatency, formatPercent } from "@/utils/format";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Dashboard — LLMOps Studio" },
      {
        name: "description",
        content:
          "Evaluation health overview: quality, latency, cost and regression pass rate across LLM experiments.",
      },
      { property: "og:title", content: "Dashboard — LLMOps Studio" },
      {
        property: "og:description",
        content: "Quality, latency, cost and regression status across your LLM experiments.",
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
      <div className="mt-4 h-[180px]">
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
        description="Quality, latency, cost and regression health across every LLM experiment in this workspace."
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
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
            <MetricCard
              label="Total Experiments"
              value={String(data.total_experiments)}
              hint="all time"
              icon={FlaskConical}
            />
            <MetricCard
              label="Evaluations This Week"
              value={String(data.evaluations_this_week)}
              hint="last 7 days"
              icon={Activity}
            />
            <MetricCard
              label="Avg Quality Score"
              value={formatPercent(data.avg_quality_score)}
              icon={Gauge}
              delta={{ value: "2.7%", direction: "down", good: false }}
            />
            <MetricCard
              label="Avg Latency"
              value={formatLatency(data.avg_latency_ms)}
              icon={Timer}
              delta={{ value: "7.3%", direction: "down", good: true }}
            />
            <MetricCard
              label="Estimated Cost"
              value={formatCost(data.estimated_cost)}
              hint="cumulative"
              icon={CircleDollarSign}
            />
            <MetricCard
              label="Regression Pass Rate"
              value={formatPercent(data.regression_pass_rate)}
              icon={ShieldCheck}
            />
          </div>

          <div className="grid gap-3 xl:grid-cols-3">
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

            <ChartCard title="Estimated Cost Over Time" subtitle="USD per run">
              <LineChart data={data.cost_over_time}>
                <CartesianGrid stroke="var(--color-border)" vertical={false} />
                <XAxis dataKey="date" {...axis} />
                <YAxis width={38} {...axis} />
                <Tooltip {...tooltipStyle} />
                <Line
                  type="monotone"
                  dataKey="cost"
                  stroke="var(--color-chart-2)"
                  strokeWidth={2}
                  dot={false}
                />
              </LineChart>
            </ChartCard>
          </div>

          <div className="grid gap-3 xl:grid-cols-[2fr_1fr]">
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
                  title="Recent Regression Alerts"
                  description="threshold breaches and warnings"
                />
              </div>
              <ul className="divide-y divide-border">
                {data.alerts.map((a) => (
                  <li key={a.id} className="space-y-2 p-4">
                    <div className="flex items-center justify-between gap-2">
                      <StatusBadge status={a.severity} />
                      <span className="num text-[11px] text-muted-foreground">
                        {formatDateTime(a.created_at)}
                      </span>
                    </div>
                    <p className="text-sm leading-relaxed">{a.message}</p>
                    <Link
                      to="/experiments/$experimentId"
                      params={{ experimentId: a.experiment_id }}
                      className="num text-xs text-primary hover:underline"
                    >
                      {a.experiment_id} →
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
