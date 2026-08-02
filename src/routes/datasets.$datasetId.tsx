import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Pencil, Plus, Trash2, Upload } from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";
import { addCase, deleteCase, getDataset, importJsonl, updateCase } from "@/api/datasets";
import { MetricCard } from "@/components/common/MetricCard";
import { PageHeader, SectionHeader } from "@/components/common/PageHeader";
import { Pill } from "@/components/common/StatusBadge";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/States";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatCategory, formatDate, truncate } from "@/utils/format";
import type { EvaluationCase, EvaluationCategory } from "@/types";

export const Route = createFileRoute("/datasets/$datasetId")({
  head: () => ({
    meta: [
      { title: "Dataset Details — LLMOps Studio" },
      { name: "description", content: "Inspect evaluation cases, categories and metadata." },
      { property: "og:title", content: "Dataset Details — LLMOps Studio" },
      { property: "og:description", content: "Evaluation cases, categories and metadata." },
    ],
  }),
  component: DatasetDetailPage,
});

const CATEGORIES: EvaluationCategory[] = [
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

function DatasetDetailPage() {
  const { datasetId } = Route.useParams();
  const queryClient = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [editing, setEditing] = useState<EvaluationCase | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({
    input: "",
    expected_output: "",
    category: "general" as EvaluationCategory,
  });

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["dataset", datasetId],
    queryFn: () => getDataset(datasetId),
  });

  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ["dataset", datasetId] });
    void queryClient.invalidateQueries({ queryKey: ["datasets"] });
  };

  const save = useMutation({
    mutationFn: () =>
      editing
        ? updateCase(datasetId, editing.id, { ...form, metadata: editing.metadata })
        : addCase(datasetId, { ...form, metadata: { source: "manual" } }),
    onSuccess: () => {
      toast.success(editing ? "Case updated" : "Case added");
      setDialogOpen(false);
      setEditing(null);
      invalidate();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const remove = useMutation({
    mutationFn: (caseId: string) => deleteCase(datasetId, caseId),
    onSuccess: () => {
      toast.success("Case deleted");
      invalidate();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const importer = useMutation({
    mutationFn: (contents: string) => importJsonl(datasetId, contents),
    onSuccess: (r) => {
      toast.success(`Imported ${r.imported} cases`);
      invalidate();
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const distribution = data
    ? Object.entries(
        data.cases.reduce<Record<string, number>>((acc, c) => {
          acc[c.category] = (acc[c.category] ?? 0) + 1;
          return acc;
        }, {}),
      ).sort((a, b) => b[1] - a[1])
    : [];

  return (
    <div className="space-y-6">
      <PageHeader
        title={data?.name ?? "Dataset"}
        description={data?.description ?? ""}
        actions={
          <>
            <input
              ref={fileRef}
              type="file"
              accept=".jsonl,.json,.txt"
              className="hidden"
              onChange={async (e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                importer.mutate(await file.text());
                e.target.value = "";
              }}
            />
            <Button variant="outline" size="sm" onClick={() => fileRef.current?.click()}>
              <Upload className="size-4" /> Import JSONL
            </Button>
            <Button
              size="sm"
              onClick={() => {
                setEditing(null);
                setForm({ input: "", expected_output: "", category: "general" });
                setDialogOpen(true);
              }}
            >
              <Plus className="size-4" /> Add Case
            </Button>
          </>
        }
      />

      {isLoading && <LoadingState rows={6} />}
      {isError && <ErrorState message={(error as Error).message} onRetry={() => void refetch()} />}

      {data && (
        <>
          <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            <MetricCard label="Examples" value={String(data.cases.length)} />
            <MetricCard label="Categories" value={String(data.categories.length)} />
            <MetricCard label="Created" value={formatDate(data.created_at)} />
            <MetricCard label="Last updated" value={formatDate(data.updated_at)} />
          </div>

          <div className="panel p-4">
            <SectionHeader title="Category distribution" description="cases per category" />
            <div className="mt-4 space-y-2">
              {distribution.map(([category, count]) => (
                <div key={category} className="flex items-center gap-3">
                  <span className="w-44 shrink-0 text-sm">{formatCategory(category)}</span>
                  <div className="h-2 flex-1 overflow-hidden rounded-sm bg-muted">
                    <div
                      className="h-full bg-primary"
                      style={{ width: `${(count / data.cases.length) * 100}%` }}
                    />
                  </div>
                  <span className="num w-10 text-right text-xs text-muted-foreground">{count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="panel">
            <div className="border-b border-border p-4">
              <SectionHeader title="Evaluation cases" description={`${data.cases.length} cases`} />
            </div>
            {data.cases.length === 0 ? (
              <EmptyState className="m-4" title="No cases in this dataset" />
            ) : (
              <div className="max-h-[560px] overflow-auto">
                <Table>
                  <TableHeader>
                    <TableRow className="hover:bg-transparent">
                      <TableHead>Input</TableHead>
                      <TableHead>Expected Output</TableHead>
                      <TableHead>Category</TableHead>
                      <TableHead>Metadata</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {data.cases.map((c) => (
                      <TableRow key={c.id}>
                        <TableCell className="max-w-[300px] text-sm">
                          {truncate(c.input, 100)}
                        </TableCell>
                        <TableCell className="max-w-[340px] text-sm text-muted-foreground">
                          {truncate(c.expected_output, 110)}
                        </TableCell>
                        <TableCell>
                          <Pill>{formatCategory(c.category)}</Pill>
                        </TableCell>
                        <TableCell className="num text-[11px] text-muted-foreground">
                          {Object.entries(c.metadata)
                            .map(([k, v]) => `${k}=${v}`)
                            .join(" · ")}
                        </TableCell>
                        <TableCell className="text-right whitespace-nowrap">
                          <Button
                            variant="ghost"
                            size="icon"
                            className="size-8"
                            aria-label="Edit case"
                            onClick={() => {
                              setEditing(c);
                              setForm({
                                input: c.input,
                                expected_output: c.expected_output,
                                category: c.category,
                              });
                              setDialogOpen(true);
                            }}
                          >
                            <Pencil className="size-3.5" />
                          </Button>
                          <Button
                            variant="ghost"
                            size="icon"
                            className="size-8"
                            aria-label="Delete case"
                            onClick={() => remove.mutate(c.id)}
                          >
                            <Trash2 className="size-3.5 text-destructive" />
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

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>{editing ? "Edit case" : "Add case"}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="case-input">Input</Label>
              <Textarea
                id="case-input"
                rows={3}
                value={form.input}
                onChange={(e) => setForm({ ...form, input: e.target.value })}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="case-expected">Expected output</Label>
              <Textarea
                id="case-expected"
                rows={3}
                value={form.expected_output}
                onChange={(e) => setForm({ ...form, expected_output: e.target.value })}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="case-category">Category</Label>
              <select
                id="case-category"
                className="h-9 w-full rounded-sm border border-input bg-transparent px-3 text-sm"
                value={form.category}
                onChange={(e) =>
                  setForm({ ...form, category: e.target.value as EvaluationCategory })
                }
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {formatCategory(c)}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => save.mutate()} disabled={save.isPending}>
              Save case
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
