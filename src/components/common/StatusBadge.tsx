import { cn } from "@/lib/utils";
import type { CaseStatus, ExperimentStatus, PromptStatus, RegressionStatus } from "@/types";

const base =
  "inline-flex items-center gap-1.5 rounded-sm border px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider";

const tones = {
  pass: "border-success/35 bg-success/12 text-success",
  fail: "border-destructive/35 bg-destructive/12 text-destructive",
  warning: "border-warning/40 bg-warning/15 text-warning",
  neutral: "border-border bg-muted text-muted-foreground",
  info: "border-primary/35 bg-primary/12 text-primary",
} as const;

export type Tone = keyof typeof tones;

export function StatusBadge({
  status,
  className,
  dot = true,
}: {
  status: RegressionStatus | CaseStatus;
  className?: string;
  dot?: boolean;
}) {
  const tone: Tone = status === "PASS" ? "pass" : status === "FAIL" ? "fail" : "warning";
  return (
    <span className={cn(base, tones[tone], className)}>
      {dot && <span className="size-1.5 rounded-full bg-current" />}
      {status}
    </span>
  );
}

export function Pill({
  children,
  tone = "neutral",
  className,
}: {
  children: React.ReactNode;
  tone?: Tone;
  className?: string;
}) {
  return <span className={cn(base, tones[tone], className)}>{children}</span>;
}

export function PromptStatusBadge({ status }: { status: PromptStatus }) {
  const tone: Tone = status === "active" ? "pass" : status === "draft" ? "info" : "neutral";
  return <Pill tone={tone}>{status}</Pill>;
}

export function RunStatusBadge({ status }: { status: ExperimentStatus }) {
  const tone: Tone = status === "completed" ? "pass" : status === "running" ? "info" : "fail";
  return <Pill tone={tone}>{status}</Pill>;
}
