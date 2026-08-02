import { Link } from "@tanstack/react-router";
import { StatusBadge } from "@/components/common/StatusBadge";
import { ProviderBadge } from "@/components/common/ProviderBadge";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCost, formatDateTime, formatLatency, formatPercent } from "@/utils/format";
import type { Experiment } from "@/types";

export function ExperimentTable({
  experiments,
  selectable = false,
  selected = [],
  onToggleSelect,
  compact = false,
}: {
  experiments: Experiment[];
  selectable?: boolean;
  selected?: string[];
  onToggleSelect?: (id: string) => void;
  compact?: boolean;
}) {
  return (
    <div className="overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow className="hover:bg-transparent">
            {selectable && <TableHead className="w-9" />}
            <TableHead>Experiment</TableHead>
            {!compact && <TableHead>Dataset</TableHead>}
            <TableHead>Provider</TableHead>
            <TableHead>Model</TableHead>
            <TableHead>Prompt</TableHead>
            <TableHead className="text-right">Quality</TableHead>
            <TableHead className="text-right">Latency</TableHead>
            <TableHead className="text-right">Cost</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Created</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {experiments.map((e) => (
            <TableRow key={e.id} className="group">
              {selectable && (
                <TableCell>
                  <Checkbox
                    checked={selected.includes(e.id)}
                    onCheckedChange={() => onToggleSelect?.(e.id)}
                    aria-label={`Select ${e.name}`}
                  />
                </TableCell>
              )}
              <TableCell className="max-w-[260px]">
                <Link
                  to="/experiments/$experimentId"
                  params={{ experimentId: e.id }}
                  className="block truncate text-sm font-medium hover:text-primary hover:underline"
                >
                  {e.name}
                </Link>
                <span className="num text-[11px] text-muted-foreground">{e.id}</span>
              </TableCell>
              {!compact && (
                <TableCell className="text-sm text-muted-foreground">{e.dataset_name}</TableCell>
              )}
              <TableCell>
                <ProviderBadge provider={e.provider} />
              </TableCell>
              <TableCell className="num text-xs text-muted-foreground">{e.model}</TableCell>
              <TableCell className="text-sm">
                <span className="text-muted-foreground">{e.prompt_name}</span>{" "}
                <span className="num font-medium">v{e.prompt_version}</span>
              </TableCell>
              <TableCell className="num text-right text-sm font-medium">
                {formatPercent(e.quality_score)}
              </TableCell>
              <TableCell className="num text-right text-sm">
                {formatLatency(e.avg_latency_ms)}
              </TableCell>
              <TableCell className="num text-right text-sm">
                {formatCost(e.estimated_cost)}
              </TableCell>
              <TableCell>
                <StatusBadge status={e.regression_status} />
              </TableCell>
              <TableCell className="num text-right text-xs text-muted-foreground">
                {formatDateTime(e.created_at)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
}
