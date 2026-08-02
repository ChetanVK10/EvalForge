import { ArrowDownRight, ArrowUpRight, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export interface MetricCardProps {
  label: string;
  value: string;
  hint?: string;
  icon?: LucideIcon;
  delta?: { value: string; direction: "up" | "down"; good: boolean };
  className?: string;
}

export function MetricCard({ label, value, hint, icon: Icon, delta, className }: MetricCardProps) {
  return (
    <div className={cn("panel flex flex-col gap-2 p-4", className)}>
      <div className="flex items-center justify-between">
        <span className="label-caps">{label}</span>
        {Icon && <Icon className="size-3.5 text-muted-foreground" strokeWidth={2} />}
      </div>
      <div className="num text-2xl leading-none font-semibold">{value}</div>
      <div className="flex items-center gap-2">
        {delta && (
          <span
            className={cn(
              "num inline-flex items-center gap-0.5 text-xs font-medium",
              delta.good ? "text-success" : "text-destructive",
            )}
          >
            {delta.direction === "up" ? (
              <ArrowUpRight className="size-3.5" />
            ) : (
              <ArrowDownRight className="size-3.5" />
            )}
            {delta.value}
          </span>
        )}
        {hint && <span className="text-xs text-muted-foreground">{hint}</span>}
      </div>
    </div>
  );
}
