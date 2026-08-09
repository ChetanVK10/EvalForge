import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { Trash2, ArrowUpDown } from "lucide-react";
import { StatusBadge } from "@/components/common/StatusBadge";
import { ProviderBadge } from "@/components/common/ProviderBadge";
import { DeleteConfirmDialog } from "@/components/common/DeleteConfirmDialog";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatDateTime, formatLatency, formatPercent } from "@/utils/format";
import type { Experiment } from "@/types";

type SortKey = "created" | "quality" | "latency" | "name";
type SortOrder = "asc" | "desc";

export function ExperimentTable({
  experiments,
  selectable = false,
  selected = [],
  onToggleSelect,
  compact = false,
  onDelete,
}: {
  experiments: Experiment[];
  selectable?: boolean;
  selected?: string[];
  onToggleSelect?: (id: string) => void;
  compact?: boolean;
  onDelete?: (id: string) => Promise<void> | void;
}) {
  const [sortKey, setSortKey] = useState<SortKey>("created");
  const [sortOrder, setSortOrder] = useState<SortOrder>("desc");
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortOrder(key === "name" ? "asc" : "desc");
    }
  };

  const sortedExperiments = [...experiments].sort((a, b) => {
    let comp = 0;
    if (sortKey === "quality") {
      const aVal = a.quality_score ?? -1;
      const bVal = b.quality_score ?? -1;
      comp = aVal - bVal;
    } else if (sortKey === "latency") {
      const aVal = a.avg_latency_ms ?? 999999;
      const bVal = b.avg_latency_ms ?? 999999;
      comp = aVal - bVal;
    } else if (sortKey === "name") {
      comp = a.name.localeCompare(b.name);
    } else {
      const aVal = new Date(a.created_at).getTime();
      const bVal = new Date(b.created_at).getTime();
      comp = aVal - bVal;
    }
    return sortOrder === "asc" ? comp : -comp;
  });

  const activeExp = experiments.find((e) => e.id === deletingId);

  const handleConfirmDelete = async () => {
    if (!deletingId || !onDelete) return;
    setIsDeleting(true);
    try {
      await onDelete(deletingId);
    } finally {
      setIsDeleting(false);
      setDeletingId(null);
    }
  };

  return (
    <>
      <div className="overflow-x-auto">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              {selectable && <TableHead className="w-9" />}
              <TableHead>
                <button
                  type="button"
                  onClick={() => toggleSort("name")}
                  className="flex items-center gap-1 font-semibold hover:text-foreground"
                >
                  Experiment <ArrowUpDown className="size-3" />
                </button>
              </TableHead>
              {!compact && <TableHead>Dataset</TableHead>}
              <TableHead>Provider</TableHead>
              <TableHead>Model</TableHead>
              <TableHead>Model Config</TableHead>
              <TableHead>Prompt</TableHead>
              <TableHead className="text-right">
                <button
                  type="button"
                  onClick={() => toggleSort("quality")}
                  className="ml-auto flex items-center gap-1 font-semibold hover:text-foreground"
                >
                  Quality <ArrowUpDown className="size-3" />
                </button>
              </TableHead>
              <TableHead className="text-right">
                <button
                  type="button"
                  onClick={() => toggleSort("latency")}
                  className="ml-auto flex items-center gap-1 font-semibold hover:text-foreground"
                >
                  Latency <ArrowUpDown className="size-3" />
                </button>
              </TableHead>
              <TableHead>Status</TableHead>
              <TableHead className="text-right">
                <button
                  type="button"
                  onClick={() => toggleSort("created")}
                  className="ml-auto flex items-center gap-1 font-semibold hover:text-foreground"
                >
                  Created <ArrowUpDown className="size-3" />
                </button>
              </TableHead>
              {onDelete && <TableHead className="w-10 text-right" />}
            </TableRow>
          </TableHeader>
          <TableBody>
            {sortedExperiments.map((e) => (
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
                  {e.model_config_id ? (
                    <Link
                      to="/configurations"
                      search={{ tab: "models", highlight: e.model_config_id }}
                      className="max-w-[150px] block truncate text-xs font-medium text-primary hover:underline"
                    >
                      {e.model_config_name || "Model Config"}
                    </Link>
                  ) : (
                    <span className="text-xs text-muted-foreground italic">
                      {e.model_config_name || "Unavailable"}
                    </span>
                  )}
                </TableCell>
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
                <TableCell>
                  <StatusBadge status={e.result_status || e.regression_status} />
                </TableCell>
                <TableCell className="num text-right text-xs text-muted-foreground">
                  {formatDateTime(e.created_at)}
                </TableCell>
                {onDelete && (
                  <TableCell className="text-right">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="size-7 text-muted-foreground hover:text-destructive"
                      onClick={() => setDeletingId(e.id)}
                      aria-label={`Delete experiment ${e.name}`}
                    >
                      <Trash2 className="size-3.5" />
                    </Button>
                  </TableCell>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {onDelete && activeExp && (
        <DeleteConfirmDialog
          open={!!deletingId}
          onOpenChange={(open) => !open && setDeletingId(null)}
          title={`Delete experiment "${activeExp.name}"?`}
          description="This permanently removes this experiment and its evaluation results. This action cannot be undone."
          onConfirm={handleConfirmDelete}
          isDeleting={isDeleting}
        />
      )}
    </>
  );
}
