import { StatusBadge } from "@/components/common/StatusBadge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import { formatCost, formatDelta, formatLatency, formatPercent } from "@/utils/format";
import type { RegressionMetric } from "@/types";

function value(metric: RegressionMetric, raw: number): string {
  if (metric.unit === "ms") return formatLatency(raw);
  if (metric.unit === "usd") return formatCost(raw);
  return formatPercent(raw);
}

function isImprovement(metric: RegressionMetric): boolean {
  return metric.direction === "higher_is_better" ? metric.delta_pct > 0 : metric.delta_pct < 0;
}

export function MetricComparisonTable({ metrics }: { metrics: RegressionMetric[] }) {
  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            <TableHead>Metric</TableHead>
            <TableHead className="text-right">Baseline</TableHead>
            <TableHead className="text-right">Candidate</TableHead>
            <TableHead className="text-right">Difference</TableHead>
            <TableHead className="text-right">Threshold</TableHead>
            <TableHead className="text-right">Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {metrics.map((m) => {
            const good = isImprovement(m);
            const neutral = Math.abs(m.delta_pct) < 0.5;
            return (
              <TableRow key={m.key}>
                <TableCell className="text-sm font-medium">{m.label}</TableCell>
                <TableCell className="num text-right text-sm">{value(m, m.baseline)}</TableCell>
                <TableCell className="num text-right text-sm font-medium">
                  {value(m, m.candidate)}
                </TableCell>
                <TableCell
                  className={cn(
                    "num text-right text-sm font-semibold",
                    neutral ? "text-muted-foreground" : good ? "text-success" : "text-destructive",
                  )}
                >
                  {formatDelta(m.delta_pct)}
                </TableCell>
                <TableCell className="num text-right text-sm text-muted-foreground">
                  {formatDelta(m.threshold_pct)}
                </TableCell>
                <TableCell className="text-right">
                  <StatusBadge status={m.status} dot={false} />
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
