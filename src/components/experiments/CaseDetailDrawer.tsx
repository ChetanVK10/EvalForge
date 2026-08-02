import { StatusBadge } from "@/components/common/StatusBadge";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { formatCategory, formatLatency, formatPercent, formatTokens } from "@/utils/format";
import type { EvaluationCaseResult } from "@/types";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <p className="label-caps mb-1.5">{label}</p>
      <div className="rounded-sm border border-border bg-muted/40 p-3 text-sm leading-relaxed">
        {children}
      </div>
    </div>
  );
}

export function CaseDetailDrawer({
  caseResult,
  open,
  onOpenChange,
}: {
  caseResult: EvaluationCaseResult | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-xl">
        {caseResult && (
          <>
            <SheetHeader className="space-y-2">
              <div className="flex items-center gap-2">
                <StatusBadge status={caseResult.status} />
                <span className="num text-xs text-muted-foreground">{caseResult.case_id}</span>
              </div>
              <SheetTitle className="text-base">
                {formatCategory(caseResult.category)} case
              </SheetTitle>
              <SheetDescription>
                Scored {formatPercent(caseResult.score)} · {formatLatency(caseResult.latency_ms)} ·{" "}
                {formatTokens(caseResult.tokens)} tokens
              </SheetDescription>
            </SheetHeader>

            <div className="space-y-4 px-4 pb-8">
              <Field label="Input">{caseResult.input}</Field>
              <Field label="Expected output">{caseResult.expected_output}</Field>
              <Field label="Actual model output">{caseResult.model_output}</Field>

              <div>
                <p className="label-caps mb-1.5">Metric scores</p>
                <div className="divide-y divide-border rounded-sm border border-border">
                  {caseResult.metric_scores.map((m) => (
                    <div key={m.key} className="flex items-center justify-between px-3 py-2">
                      <span className="text-sm">{m.label}</span>
                      <span className="num text-sm font-medium">{formatPercent(m.score)}</span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="panel p-3">
                  <p className="label-caps">Latency</p>
                  <p className="num mt-1 text-lg font-semibold">
                    {formatLatency(caseResult.latency_ms)}
                  </p>
                </div>
                <div className="panel p-3">
                  <p className="label-caps">Token usage</p>
                  <p className="num mt-1 text-lg font-semibold">
                    {formatTokens(caseResult.tokens)}
                  </p>
                </div>
              </div>

              {caseResult.failure_reason && (
                <div className="rounded-sm border border-destructive/30 bg-destructive/5 p-3">
                  <p className="label-caps text-destructive">Failure reason</p>
                  <p className="mt-1 text-sm">{caseResult.failure_reason}</p>
                </div>
              )}

              <Field label="LLM judge explanation">{caseResult.judge_explanation}</Field>
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  );
}
