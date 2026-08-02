import { AlertTriangle, Inbox, Loader2 } from "lucide-react";
import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export function LoadingState({
  label = "Loading…",
  rows = 5,
  variant = "table",
  className,
}: {
  label?: string;
  rows?: number;
  variant?: "table" | "inline" | "cards";
  className?: string;
}) {
  if (variant === "inline") {
    return (
      <div
        className={cn("flex items-center gap-2 p-6 text-sm text-muted-foreground", className)}
        role="status"
      >
        <Loader2 className="size-4 animate-spin" />
        {label}
      </div>
    );
  }
  if (variant === "cards") {
    return (
      <div className={cn("grid gap-3 sm:grid-cols-2 xl:grid-cols-3", className)} role="status">
        {Array.from({ length: rows }).map((_, i) => (
          <Skeleton key={i} className="h-28 w-full rounded-md" />
        ))}
      </div>
    );
  }
  return (
    <div className={cn("space-y-2 p-4", className)} role="status" aria-label={label}>
      {Array.from({ length: rows }).map((_, i) => (
        <Skeleton key={i} className="h-9 w-full rounded-sm" />
      ))}
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  message,
  onRetry,
  className,
}: {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-md border border-destructive/30 bg-destructive/5 p-10 text-center",
        className,
      )}
      role="alert"
    >
      <AlertTriangle className="size-6 text-destructive" />
      <div>
        <p className="text-sm font-semibold">{title}</p>
        {message && <p className="mt-1 max-w-md text-sm text-muted-foreground">{message}</p>}
      </div>
      {onRetry && (
        <Button size="sm" variant="outline" onClick={onRetry}>
          Retry
        </Button>
      )}
    </div>
  );
}

export function EmptyState({
  title,
  message,
  action,
  className,
}: {
  title: string;
  message?: string;
  action?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-3 rounded-md border border-dashed border-border-strong p-12 text-center",
        className,
      )}
    >
      <Inbox className="size-6 text-muted-foreground" />
      <div>
        <p className="text-sm font-semibold">{title}</p>
        {message && <p className="mt-1 max-w-md text-sm text-muted-foreground">{message}</p>}
      </div>
      {action}
    </div>
  );
}
