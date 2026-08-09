import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import {
  createModelConfiguration,
  createPromptConfiguration,
  createPromptVersion,
  deleteModelConfiguration,
  deletePromptConfiguration,
  listModelConfigurations,
  listPromptConfigurations,
  updateModelConfiguration,
  updatePromptConfiguration,
  updatePromptVersion,
} from "@/api/configurations";
import { getSettings } from "@/api/settings";
import { DeleteConfirmDialog } from "@/components/common/DeleteConfirmDialog";
import { PageHeader, SectionHeader } from "@/components/common/PageHeader";
import { ProviderBadge } from "@/components/common/ProviderBadge";
import { PromptStatusBadge } from "@/components/common/StatusBadge";
import { ErrorState, LoadingState } from "@/components/common/States";
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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { formatDate, truncate } from "@/utils/format";
import type { ModelConfiguration, PromptConfiguration, PromptStatus, Provider } from "@/types";

interface ConfigurationsSearch {
  tab?: "models" | "prompts";
  highlight?: string;
}

export const Route = createFileRoute("/configurations")({
  validateSearch: (search: Record<string, unknown>): ConfigurationsSearch => {
    const tabVal = search["tab"];
    const highlightVal = search["highlight"];
    return {
      tab: tabVal === "prompts" ? "prompts" : "models",
      ...(typeof highlightVal === "string" ? { highlight: highlightVal } : {}),
    };
  },
  head: () => ({
    meta: [
      { title: "Configurations — LLMOps Studio" },
      {
        name: "description",
        content: "Model and versioned prompt configurations used by evaluation runs.",
      },
      { property: "og:title", content: "Configurations — LLMOps Studio" },
      { property: "og:description", content: "Model settings and versioned prompts." },
    ],
  }),
  component: ConfigurationsPage,
});

function ConfigurationsPage() {
  const { tab = "models", highlight } = Route.useSearch();
  const queryClient = useQueryClient();
  const models = useQuery({ queryKey: ["model-configs"], queryFn: listModelConfigurations });
  const prompts = useQuery({ queryKey: ["prompt-configs"], queryFn: listPromptConfigurations });
  const settings = useQuery({ queryKey: ["settings"], queryFn: getSettings });

  const [modelOpen, setModelOpen] = useState(false);
  const [modelForm, setModelForm] = useState({
    name: "",
    provider: "groq" as Provider,
    model: "llama-3.3-70b-versatile",
    temperature: 0.2,
    max_tokens: 1024,
  });

  const [editModelOpen, setEditModelOpen] = useState(false);
  const [editingModel, setEditingModel] = useState<ModelConfiguration | null>(null);
  const [editModelForm, setEditModelForm] = useState({
    name: "",
    provider: "groq" as Provider,
    model: "",
    temperature: 0.2,
    max_tokens: 1024,
  });

  const [promptOpen, setPromptOpen] = useState(false);
  const [promptMode, setPromptMode] = useState<"create" | "version" | "edit">("create");
  const [activePrompt, setActivePrompt] = useState<PromptConfiguration | null>(null);
  const [promptForm, setPromptForm] = useState({
    name: "",
    status: "draft" as PromptStatus,
    system_prompt: "",
    user_template: "{{input}}",
    notes: "",
  });
  const [historyOf, setHistoryOf] = useState<PromptConfiguration | null>(null);
  const [deletingModel, setDeletingModel] = useState<{ id: string; name: string } | null>(null);
  const [deletingPrompt, setDeletingPrompt] = useState<{ id: string; name: string } | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDeleteModel = async () => {
    if (!deletingModel) return;
    setIsDeleting(true);
    try {
      await deleteModelConfiguration(deletingModel.id);
      toast.success("Model configuration deleted successfully.");
      void queryClient.invalidateQueries({ queryKey: ["model-configs"] });
      setDeletingModel(null);
    } catch (err: any) {
      toast.error(err.message || "Failed to delete model configuration.");
    } finally {
      setIsDeleting(false);
    }
  };

  const handleDeletePrompt = async () => {
    if (!deletingPrompt) return;
    setIsDeleting(true);
    try {
      await deletePromptConfiguration(deletingPrompt.id);
      toast.success("Prompt configuration deleted successfully.");
      void queryClient.invalidateQueries({ queryKey: ["prompt-configs"] });
      setDeletingPrompt(null);
    } catch (err: any) {
      toast.error(err.message || "Failed to delete prompt configuration.");
    } finally {
      setIsDeleting(false);
    }
  };

  const getModelsForProvider = (prov: Provider): string[] => {
    const fromSettings = settings.data?.providers.find((p) => p.provider === prov)?.models;
    if (fromSettings && fromSettings.length > 0) return fromSettings;
    return prov === "gemini"
      ? ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]
      : ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"];
  };

  const providerModels = getModelsForProvider(modelForm.provider);
  const editProviderModels = editingModel ? getModelsForProvider(editingModel.provider) : [];

  const openNewModelModal = () => {
    const defaultProvider: Provider = "groq";
    const available = getModelsForProvider(defaultProvider);
    setModelForm({
      name: "",
      provider: defaultProvider,
      model: available[0] ?? "llama-3.3-70b-versatile",
      temperature: 0.2,
      max_tokens: 1024,
    });
    setModelOpen(true);
  };

  const openEditModelModal = (m: ModelConfiguration) => {
    setEditingModel(m);
    setEditModelForm({
      name: m.name,
      provider: m.provider,
      model: m.model,
      temperature: m.temperature,
      max_tokens: m.max_tokens,
    });
    setEditModelOpen(true);
  };

  const saveModel = useMutation({
    mutationFn: () => createModelConfiguration(modelForm),
    onSuccess: () => {
      toast.success("Model configuration created");
      setModelOpen(false);
      void queryClient.invalidateQueries({ queryKey: ["model-configs"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const updateModel = useMutation({
    mutationFn: () => {
      if (!editingModel) throw new Error("No model configuration selected.");
      if (!editModelForm.name.trim()) throw new Error("Configuration name is required.");
      if (editModelForm.temperature < 0.0 || editModelForm.temperature > 2.0) {
        throw new Error("Temperature must be between 0.0 and 2.0");
      }
      if (!Number.isInteger(editModelForm.max_tokens) || editModelForm.max_tokens <= 0) {
        throw new Error("Max tokens must be a positive integer");
      }
      return updateModelConfiguration(editingModel.id, {
        name: editModelForm.name.trim(),
        model: editModelForm.model.trim(),
        temperature: editModelForm.temperature,
        max_tokens: editModelForm.max_tokens,
      });
    },
    onSuccess: () => {
      toast.success("Model configuration updated successfully.");
      setEditModelOpen(false);
      setEditingModel(null);
      void queryClient.invalidateQueries({ queryKey: ["model-configs"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const savePrompt = useMutation({
    mutationFn: async (): Promise<void> => {
      const body = {
        system_prompt: promptForm.system_prompt,
        user_template: promptForm.user_template,
        notes: promptForm.notes,
      };
      if (promptMode === "create") {
        await createPromptConfiguration(promptForm);
        return;
      }
      if (!activePrompt) throw new Error("No prompt selected.");
      if (promptMode === "edit") {
        if (!promptForm.name.trim()) throw new Error("Prompt configuration name is required.");
        await updatePromptConfiguration(activePrompt.id, { name: promptForm.name.trim() });
        return;
      }
      if (promptMode === "version") {
        await createPromptVersion(activePrompt.id, body);
        return;
      }
    },
    onSuccess: () => {
      toast.success(
        promptMode === "edit"
          ? "Prompt configuration updated"
          : promptMode === "version"
            ? "New prompt version created"
            : "Prompt created",
      );
      setPromptOpen(false);
      void queryClient.invalidateQueries({ queryKey: ["prompt-configs"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const openPrompt = (mode: typeof promptMode, prompt?: PromptConfiguration) => {
    setPromptMode(mode);
    setActivePrompt(prompt ?? null);
    const latest = prompt?.versions.at(-1);
    setPromptForm({
      name: prompt?.name ?? "",
      status: prompt?.status ?? "draft",
      system_prompt: mode === "create" ? "" : (latest?.system_prompt ?? ""),
      user_template: mode === "create" ? "{{input}}" : (latest?.user_template ?? "{{input}}"),
      notes: "",
    });
    setPromptOpen(true);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Configurations"
        description="Model settings and versioned prompts. Provider credentials are managed by the backend environment, never in the browser."
      />

      <Tabs defaultValue={tab}>
        <TabsList>
          <TabsTrigger value="models">Model Configurations</TabsTrigger>
          <TabsTrigger value="prompts">Prompt Configurations</TabsTrigger>
        </TabsList>

        <TabsContent value="models" className="mt-4 space-y-3">
          <SectionHeader
            title="Model configurations"
            description="reusable provider + decoding settings"
            actions={
              <Button size="sm" onClick={openNewModelModal}>
                <Plus className="size-4" /> New model config
              </Button>
            }
          />
          <div className="panel">
            {models.isLoading && <LoadingState rows={3} />}
            {models.isError && (
              <ErrorState
                className="m-4"
                message={(models.error as Error).message}
                onRetry={() => void models.refetch()}
              />
            )}
            {models.data && (
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead>Configuration</TableHead>
                    <TableHead>Provider</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead className="text-right">Temperature</TableHead>
                    <TableHead className="text-right">Max tokens</TableHead>
                    <TableHead className="text-right">Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {models.data.map((m) => (
                    <TableRow
                      key={m.id}
                      className={cn(
                        m.id === highlight && "bg-accent/40 font-semibold ring-1 ring-primary/40",
                      )}
                    >
                      <TableCell className="text-sm font-medium">{m.name}</TableCell>
                      <TableCell>
                        <ProviderBadge provider={m.provider} />
                      </TableCell>
                      <TableCell className="num text-xs text-muted-foreground">{m.model}</TableCell>
                      <TableCell className="num text-right text-sm">{m.temperature}</TableCell>
                      <TableCell className="num text-right text-sm">{m.max_tokens}</TableCell>
                      <TableCell className="num text-right text-xs text-muted-foreground">
                        {formatDate(m.created_at)}
                      </TableCell>
                      <TableCell className="text-right whitespace-nowrap">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openEditModelModal(m)}
                          aria-label={`Edit model configuration ${m.name}`}
                        >
                          Edit
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="size-7 text-muted-foreground hover:text-destructive inline-flex ml-1 align-middle"
                          onClick={() => setDeletingModel({ id: m.id, name: m.name })}
                          aria-label={`Delete model configuration ${m.name}`}
                        >
                          <Trash2 className="size-3.5" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </TabsContent>

        <TabsContent value="prompts" className="mt-4 space-y-3">
          <SectionHeader
            title="Prompt configurations"
            description="versioned prompts compared during regression testing"
            actions={
              <Button size="sm" onClick={() => openPrompt("create")}>
                <Plus className="size-4" /> New prompt
              </Button>
            }
          />
          <div className="panel">
            {prompts.isLoading && <LoadingState rows={3} />}
            {prompts.isError && (
              <ErrorState
                className="m-4"
                message={(prompts.error as Error).message}
                onRetry={() => void prompts.refetch()}
              />
            )}
            {prompts.data && (
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent">
                    <TableHead>Prompt</TableHead>
                    <TableHead className="text-right">Version</TableHead>
                    <TableHead>System prompt preview</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Created</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {prompts.data.map((p) => (
                    <TableRow key={p.id}>
                      <TableCell className="text-sm font-medium">{p.name}</TableCell>
                      <TableCell className="num text-right text-sm">v{p.latest_version}</TableCell>
                      <TableCell className="max-w-[380px] text-sm text-muted-foreground">
                        {truncate(p.versions.at(-1)?.system_prompt ?? "", 110)}
                      </TableCell>
                      <TableCell>
                        <PromptStatusBadge status={p.status} />
                      </TableCell>
                      <TableCell className="num text-right text-xs text-muted-foreground">
                        {formatDate(p.created_at)}
                      </TableCell>
                      <TableCell className="text-right whitespace-nowrap">
                        <Button variant="ghost" size="sm" onClick={() => openPrompt("edit", p)}>
                          Edit
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => openPrompt("version", p)}>
                          New version
                        </Button>
                        <Button variant="ghost" size="sm" onClick={() => setHistoryOf(p)}>
                          History
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="size-7 text-muted-foreground hover:text-destructive inline-flex ml-1 align-middle"
                          onClick={() => setDeletingPrompt({ id: p.id, name: p.name })}
                          aria-label={`Delete prompt configuration ${p.name}`}
                        >
                          <Trash2 className="size-3.5" />
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )}
          </div>
        </TabsContent>
      </Tabs>

      <Dialog open={modelOpen} onOpenChange={setModelOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>New model configuration</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="mc-name">Configuration name</Label>
              <Input
                id="mc-name"
                value={modelForm.name}
                onChange={(e) => setModelForm({ ...modelForm, name: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="mc-provider">Provider</Label>
                <select
                  id="mc-provider"
                  className="h-9 w-full rounded-sm border border-input bg-transparent px-3 text-sm"
                  value={modelForm.provider}
                  onChange={(e) => {
                    const nextProvider = e.target.value as Provider;
                    const availableModels = getModelsForProvider(nextProvider);
                    const nextModel = availableModels.includes(modelForm.model)
                      ? modelForm.model
                      : (availableModels[0] ?? "");
                    setModelForm({
                      ...modelForm,
                      provider: nextProvider,
                      model: nextModel,
                    });
                  }}
                >
                  <option value="groq">Groq</option>
                  <option value="gemini">Google Gemini</option>
                </select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="mc-model">Model</Label>
                <select
                  id="mc-model"
                  className="h-9 w-full rounded-sm border border-input bg-transparent px-3 text-sm"
                  value={modelForm.model}
                  onChange={(e) => setModelForm({ ...modelForm, model: e.target.value })}
                >
                  {providerModels.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="mc-temp">Temperature</Label>
                <Input
                  id="mc-temp"
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  value={modelForm.temperature}
                  onChange={(e) =>
                    setModelForm({ ...modelForm, temperature: Number(e.target.value) })
                  }
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="mc-tokens">Max tokens</Label>
                <Input
                  id="mc-tokens"
                  type="number"
                  step="128"
                  value={modelForm.max_tokens}
                  onChange={(e) =>
                    setModelForm({ ...modelForm, max_tokens: Number(e.target.value) })
                  }
                />
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              API keys are configured server-side and are never entered or stored here.
            </p>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setModelOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => saveModel.mutate()} disabled={saveModel.isPending}>
              Create configuration
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={editModelOpen} onOpenChange={setEditModelOpen}>
        <DialogContent className="sm:max-w-lg">
          <DialogHeader>
            <DialogTitle>Edit Model Configuration</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="edit-mc-name">Configuration name</Label>
              <Input
                id="edit-mc-name"
                value={editModelForm.name}
                onChange={(e) => setEditModelForm({ ...editModelForm, name: e.target.value })}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="edit-mc-provider">Provider</Label>
                <Input
                  id="edit-mc-provider"
                  value={editModelForm.provider === "gemini" ? "Google Gemini" : "Groq"}
                  disabled
                  className="bg-muted text-muted-foreground cursor-not-allowed"
                />
                <p className="text-[11px] text-muted-foreground">
                  Provider cannot be changed after creation. Create a new configuration to use a
                  different provider.
                </p>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="edit-mc-model">Model</Label>
                <select
                  id="edit-mc-model"
                  className="h-9 w-full rounded-sm border border-input bg-transparent px-3 text-sm"
                  value={editModelForm.model}
                  onChange={(e) => setEditModelForm({ ...editModelForm, model: e.target.value })}
                >
                  {editProviderModels.map((m) => (
                    <option key={m} value={m}>
                      {m}
                    </option>
                  ))}
                </select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="edit-mc-temp">Temperature</Label>
                <Input
                  id="edit-mc-temp"
                  type="number"
                  step="0.1"
                  min="0"
                  max="2"
                  value={editModelForm.temperature}
                  onChange={(e) =>
                    setEditModelForm({ ...editModelForm, temperature: Number(e.target.value) })
                  }
                />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="edit-mc-tokens">Max tokens</Label>
                <Input
                  id="edit-mc-tokens"
                  type="number"
                  step="128"
                  value={editModelForm.max_tokens}
                  onChange={(e) =>
                    setEditModelForm({ ...editModelForm, max_tokens: Number(e.target.value) })
                  }
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditModelOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => updateModel.mutate()} disabled={updateModel.isPending}>
              Save changes
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={promptOpen} onOpenChange={setPromptOpen}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>
              {promptMode === "create"
                ? "New prompt"
                : promptMode === "version"
                  ? `New version of ${activePrompt?.name}`
                  : `Edit ${activePrompt?.name}`}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            {promptMode === "edit" && (
              <div className="space-y-1.5">
                <Label htmlFor="p-name">Prompt configuration name</Label>
                <Input
                  id="p-name"
                  value={promptForm.name}
                  onChange={(e) => setPromptForm({ ...promptForm, name: e.target.value })}
                  placeholder="e.g. Customer Support Policy Prompt"
                />
              </div>
            )}
            {promptMode === "create" && (
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label htmlFor="p-name">Prompt name</Label>
                  <Input
                    id="p-name"
                    value={promptForm.name}
                    onChange={(e) => setPromptForm({ ...promptForm, name: e.target.value })}
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="p-status">Status</Label>
                  <select
                    id="p-status"
                    className="h-9 w-full rounded-sm border border-input bg-transparent px-3 text-sm"
                    value={promptForm.status}
                    onChange={(e) =>
                      setPromptForm({ ...promptForm, status: e.target.value as PromptStatus })
                    }
                  >
                    <option value="draft">Draft</option>
                    <option value="active">Active</option>
                    <option value="archived">Archived</option>
                  </select>
                </div>
              </div>
            )}
            <div className="space-y-1.5">
              <Label htmlFor="p-system">System prompt</Label>
              <Textarea
                id="p-system"
                rows={6}
                value={promptForm.system_prompt}
                onChange={(e) => setPromptForm({ ...promptForm, system_prompt: e.target.value })}
                disabled={promptMode === "edit"}
                className={cn(
                  promptMode === "edit" && "bg-muted cursor-not-allowed text-muted-foreground",
                )}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="p-template">User template</Label>
              <Textarea
                id="p-template"
                rows={3}
                value={promptForm.user_template}
                onChange={(e) => setPromptForm({ ...promptForm, user_template: e.target.value })}
                disabled={promptMode === "edit"}
                className={cn(
                  promptMode === "edit" && "bg-muted cursor-not-allowed text-muted-foreground",
                )}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="p-notes">Change notes</Label>
              <Input
                id="p-notes"
                value={promptForm.notes}
                onChange={(e) => setPromptForm({ ...promptForm, notes: e.target.value })}
                disabled={promptMode === "edit"}
                className={cn(
                  promptMode === "edit" && "bg-muted cursor-not-allowed text-muted-foreground",
                )}
              />
            </div>
            {promptMode === "edit" && (
              <p className="text-xs text-muted-foreground">
                Version content is read-only in Edit mode. To modify system prompt or user template,
                use <strong>New version</strong>.
              </p>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setPromptOpen(false)}>
              Cancel
            </Button>
            <Button onClick={() => savePrompt.mutate()} disabled={savePrompt.isPending}>
              Save prompt
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={historyOf !== null} onOpenChange={(o) => !o && setHistoryOf(null)}>
        <DialogContent className="sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>{historyOf?.name} — version history</DialogTitle>
          </DialogHeader>
          <ol className="max-h-[420px] space-y-3 overflow-y-auto">
            {historyOf?.versions
              .slice()
              .reverse()
              .map((v) => (
                <li key={v.id} className="rounded-sm border border-border p-3">
                  <div className="flex items-center justify-between">
                    <span className="num text-sm font-semibold">v{v.version}</span>
                    <span className="num text-[11px] text-muted-foreground">
                      {formatDate(v.created_at)}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{v.notes}</p>
                  <p className="mt-2 text-sm leading-relaxed">{v.system_prompt}</p>
                </li>
              ))}
          </ol>
        </DialogContent>
      </Dialog>

      <DeleteConfirmDialog
        open={deletingModel !== null}
        onOpenChange={(open) => !open && setDeletingModel(null)}
        title={`Delete model configuration "${deletingModel?.name ?? ""}"?`}
        description="This permanently removes this model configuration. This action cannot be undone."
        onConfirm={handleDeleteModel}
        isDeleting={isDeleting}
      />

      <DeleteConfirmDialog
        open={deletingPrompt !== null}
        onOpenChange={(open) => !open && setDeletingPrompt(null)}
        title={`Delete prompt configuration "${deletingPrompt?.name ?? ""}"?`}
        description="This permanently removes this prompt configuration and its version history. This action cannot be undone."
        onConfirm={handleDeletePrompt}
        isDeleting={isDeleting}
      />
    </div>
  );
}
