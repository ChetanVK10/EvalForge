export function formatNumber(value: number, digits = 1): string {
  return value.toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function formatPercent(value: number, digits = 1): string {
  return `${formatNumber(value, digits)}%`;
}

export function formatDelta(value: number, digits = 1, suffix = "%"): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${formatNumber(value, digits)}${suffix}`;
}

export function formatLatency(ms: number): string {
  return ms >= 1000 ? `${(ms / 1000).toFixed(2)} s` : `${Math.round(ms)} ms`;
}

export function formatCost(usd: number): string {
  return `$${usd.toFixed(usd < 1 ? 3 : 2)}`;
}

export function formatTokens(tokens: number): string {
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(2)}M`;
  if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(1)}K`;
  return String(tokens);
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateTime(iso: string): string {
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatCategory(category: string): string {
  return category
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function truncate(text: string, max = 90): string {
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
}

export const METRIC_OPTIONS = [
  {
    value: "exact_match",
    label: "Exact Match",
    hint: "Strict string equality after normalization",
  },
  { value: "keyword_match", label: "Keyword Match", hint: "Required keywords present in output" },
  {
    value: "semantic_similarity",
    label: "Semantic Similarity",
    hint: "Embedding cosine similarity vs. reference",
  },
  { value: "llm_judge", label: "LLM Judge", hint: "Rubric-graded by a judge model" },
  {
    value: "response_completeness",
    label: "Response Completeness",
    hint: "Coverage of required reference facts",
  },
] as const;
