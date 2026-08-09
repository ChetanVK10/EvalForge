import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { createDataset, deleteDataset, listDatasets } from "@/api/datasets";
import { DeleteConfirmDialog } from "@/components/common/DeleteConfirmDialog";
import { PageHeader } from "@/components/common/PageHeader";
import { Pill } from "@/components/common/StatusBadge";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/States";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
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
import { formatCategory, formatDate, normalizeCategory } from "@/utils/format";
import type { EvaluationCategory } from "@/types";

export const Route = createFileRoute("/datasets/")({
  head: () => ({
    meta: [
      { title: "Datasets — LLMOps Studio" },
      {
        name: "description",
        content: "Manage LLM evaluation datasets, cases and category coverage.",
      },
      { property: "og:title", content: "Datasets — LLMOps Studio" },
      { property: "og:description", content: "Evaluation datasets and case coverage." },
    ],
  }),
  component: DatasetsPage,
});

function DatasetsPage() {
  const queryClient = useQueryClient();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [cases, setCases] = useState("");
  const [deletingDataset, setDeletingDataset] = useState<{ id: string; name: string } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const { data, isLoading, isError, error, refetch } = useQuery({
    queryKey: ["datasets"],
    queryFn: listDatasets,
  });

  const handleDeleteDataset = async () => {
    if (!deletingDataset) return;
    setIsDeleting(true);
    try {
      await deleteDataset(deletingDataset.id);
      toast.success("Dataset deleted successfully.");
      void queryClient.invalidateQueries({ queryKey: ["datasets"] });
      setDeletingDataset(null);
    } catch (err: any) {
      toast.error(err.message || "Failed to delete dataset.");
    } finally {
      setIsDeleting(false);
    }
  };

  const create = useMutation({
    mutationFn: () =>
      createDataset({
        name,
        description,
        cases: cases
          .split("\n")
          .map((l) => l.trim())
          .filter(Boolean)
          .map((line) => {
            const [input, expected, category] = line.split("|").map((p) => p.trim());
            return {
              input: input ?? line,
              expected_output: expected ?? "",
              category: normalizeCategory(category ?? "general") as EvaluationCategory,
              metadata: {},
            };
          }),
      }),
    onSuccess: (ds) => {
      toast.success(`Dataset "${ds.name}" created`);
      setOpen(false);
      setName("");
      setDescription("");
      setCases("");
      void queryClient.invalidateQueries({ queryKey: ["datasets"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title="Datasets"
        description="Curated evaluation sets used by experiments. Each case pairs an input with a reference answer and a category."
        actions={
          <Button size="sm" onClick={() => setOpen(true)}>
            <Plus className="size-4" /> New Dataset
          </Button>
        }
      />

      <div className="panel">
        {isLoading && <LoadingState rows={4} />}
        {isError && (
          <ErrorState
            className="m-4"
            message={(error as Error).message}
            onRetry={() => void refetch()}
          />
        )}
        {data && data.length === 0 && (
          <EmptyState
            className="m-4"
            title="No datasets yet"
            message="Create a dataset to start evaluating prompts."
            action={
              <Button size="sm" onClick={() => setOpen(true)}>
                New Dataset
              </Button>
            }
          />
        )}
        {data && data.length > 0 && (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead>Dataset</TableHead>
                  <TableHead>Description</TableHead>
                  <TableHead className="text-right">Cases</TableHead>
                  <TableHead>Categories</TableHead>
                  <TableHead className="text-right">Created</TableHead>
                  <TableHead className="text-right">Updated</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.map((d) => (
                  <TableRow key={d.id}>
                    <TableCell>
                      <Link
                        to="/datasets/$datasetId"
                        params={{ datasetId: d.id }}
                        className="text-sm font-medium hover:text-primary hover:underline"
                      >
                        {d.name}
                      </Link>
                      <p className="num text-[11px] text-muted-foreground">{d.id}</p>
                    </TableCell>
                    <TableCell className="max-w-[380px] text-sm text-muted-foreground">
                      {d.description}
                    </TableCell>
                    <TableCell className="num text-right text-sm">{d.case_count}</TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {d.categories.map((c) => (
                          <Pill key={c}>{formatCategory(c)}</Pill>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell className="num text-right text-xs text-muted-foreground">
                      {formatDate(d.created_at)}
                    </TableCell>
                    <TableCell className="num text-right text-xs text-muted-foreground">
                      {formatDate(d.updated_at)}
                    </TableCell>
                    <TableCell className="text-right whitespace-nowrap">
                      <Button asChild variant="ghost" size="sm">
                        <Link to="/datasets/$datasetId" params={{ datasetId: d.id }}>
                          Open
                        </Link>
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="size-7 text-muted-foreground hover:text-destructive ml-1"
                        onClick={() => setDeletingDataset({ id: d.id, name: d.name })}
                        aria-label={`Delete dataset ${d.name}`}
                      >
                        <Trash2 className="size-3.5" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>

      <DeleteConfirmDialog
        open={deletingDataset !== null}
        onOpenChange={(open) => !open && setDeletingDataset(null)}
        title={`Delete dataset "${deletingDataset?.name ?? ""}"?`}
        description="This permanently removes this dataset and all associated test cases. This action cannot be undone."
        onConfirm={handleDeleteDataset}
        isDeleting={isDeleting}
      />

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>New dataset</DialogTitle>
            <DialogDescription>
              Add cases as one per line: input | expected output | category
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="ds-name">Dataset name</Label>
              <Input id="ds-name" value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="ds-desc">Description</Label>
              <Input
                id="ds-desc"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="ds-cases">Evaluation cases</Label>
              <Textarea
                id="ds-cases"
                rows={6}
                value={cases}
                onChange={(e) => setCases(e.target.value)}
                placeholder="Where is my refund? | Refunds post in 5-7 business days | billing"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => create.mutate()} disabled={create.isPending}>
              {create.isPending ? "Creating…" : "Create dataset"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
