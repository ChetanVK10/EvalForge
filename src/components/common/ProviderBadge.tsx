import { cn } from "@/lib/utils";
import type { Provider } from "@/types";

const providerMeta: Record<Provider, { label: string; className: string }> = {
  groq: { label: "Groq", className: "border-chart-3/40 bg-chart-3/12 text-chart-3" },
  gemini: { label: "Gemini", className: "border-chart-5/40 bg-chart-5/12 text-chart-5" },
};

export function ProviderBadge({ provider, className }: { provider: Provider; className?: string }) {
  const meta = providerMeta[provider];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-sm border px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wider",
        meta.className,
        className,
      )}
    >
      <span className="size-1.5 rounded-full bg-current" />
      {meta.label}
    </span>
  );
}
