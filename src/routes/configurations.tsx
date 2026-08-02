import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createFileRoute } from "@tanstack/react-router";
import { Plus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import {
  createModelConfiguration,
  createPromptConfiguration,
  createPromptVersion,
  listModelConfigurations,
  listPromptConfigurations,
  updatePromptVersion,
} from "@/api/configurations";
import { getSettings } from "@/api/settings";
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
import type { PromptConfiguration, PromptStatus, Provider } from "@/types";

export const Route = createFileRoute("/configurations")({
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

  const providerModels =
    settings.data?.providers.find((p) => p.provider === modelForm.provider)?.models ?? [];

  const saveModel = useMutation({
    mutationFn: () => createModelConfiguration(modelForm),
    onSuccess: () => {
      toast.success("Model configuration created");
      setModelOpen(false);
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
      if (promptMode === "version") {
        await createPromptVersion(activePrompt.id, body);
        return;
      }
      await updatePromptVersion(activePrompt.id, activePrompt.latest_version, body);
    },
    onSuccess: () => {
      toast.success("Prompt saved");
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

      <Tabs defaultValue="models">
        <TabsList>
          <TabsTrigger value="models">Model Configurations</TabsTrigger>
          <TabsTrigger value="prompts">Prompt Configurations</TabsTrigger>
        </TabsList>

        <TabsContent value="models" className="mt-4 space-y-3">
          <SectionHeader
            title="Model configurations"
            description="reusable provider + decoding settings"
            actions={
              <Button size="sm" onClick={() => setModelOpen(true)}>
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
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {models.data.map((m) => (
                    <TableRow key={m.id}>
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
                  onChange={(e) =>
                    setModelForm({ ...modelForm, provider: e.target.value as Provider })
                  }
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
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="p-template">User template</Label>
              <Textarea
                id="p-template"
                rows={3}
                value={promptForm.user_template}
                onChange={(e) => setPromptForm({ ...promptForm, user_template: e.target.value })}
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="p-notes">Change notes</Label>
              <Input
                id="p-notes"
                value={promptForm.notes}
                onChange={(e) => setPromptForm({ ...promptForm, notes: e.target.value })}
              />
            </div>
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
    </div>
  );
}
