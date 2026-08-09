/** Sentinel string rendered when a numeric metric has no measured value. */
export const UNAVAILABLE = "\u2014";

/**
 * Format a number to a fixed number of decimal places using locale grouping.
 * Returns UNAVAILABLE for null/undefined — but preserves actual 0.
 */
export function formatNumber(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined) return UNAVAILABLE;
  return value.toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

/**
 * Format a percentage value (0-100 scale).
 * Returns "—" for null/undefined. Actual 0 renders as "0.0%".
 */
export function formatPercent(value: number | null | undefined, digits = 1): string {
  if (value === null || value === undefined) return UNAVAILABLE;
  return `${formatNumber(value, digits)}%`;
}

/**
 * Format a signed delta value with a leading "+" for positive numbers.
 * Returns "—" for null/undefined.
 */
export function formatDelta(value: number | null | undefined, digits = 1, suffix = "%"): string {
  if (value === null || value === undefined) return UNAVAILABLE;
  const sign = value > 0 ? "+" : "";
  return `${sign}${formatNumber(value, digits)}${suffix}`;
}

/**
 * Format a latency value in milliseconds.
 * Returns "—" for null/undefined. Actual 0 renders as "0 ms".
 */
export function formatLatency(ms: number | null | undefined): string {
  if (ms === null || ms === undefined) return UNAVAILABLE;
  return ms >= 1000 ? `${(ms / 1000).toFixed(2)} s` : `${Math.round(ms)} ms`;
}

/**
 * Format a cost value in USD.
 * Returns "—" for null/undefined. Actual 0 renders as "$0.000".
 */
export function formatCost(usd: number | null | undefined): string {
  if (usd === null || usd === undefined || isNaN(usd)) return "N/A";
  if (usd === 0) return "$0.00";
  if (usd >= 1) return `$${usd.toFixed(2)}`;
  if (usd >= 0.01) return `$${usd.toFixed(3)}`;
  if (usd >= 0.001) return `$${usd.toFixed(4)}`;
  if (usd >= 0.0001) return `$${usd.toFixed(5)}`;
  return `$${usd.toFixed(6)}`;
}

/**
 * Format a token count with K/M suffixes.
 * Returns "—" for null/undefined. Actual 0 renders as "0".
 */
export function formatTokens(tokens: number | null | undefined): string {
  if (tokens === null || tokens === undefined) return UNAVAILABLE;
  if (tokens >= 1_000_000) return `${(tokens / 1_000_000).toFixed(2)}M`;
  if (tokens >= 1_000) return `${(tokens / 1_000).toFixed(1)}K`;
  return String(tokens);
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return UNAVAILABLE;
  return new Date(iso).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return UNAVAILABLE;
  return new Date(iso).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export const STANDARD_CATEGORIES = [
  { value: "general", label: "General" },
  { value: "customer-support", label: "Customer Support" },
  { value: "billing", label: "Billing" },
  { value: "technical", label: "Technical Support" },
  { value: "account-management", label: "Account Management" },
  { value: "factuality", label: "Factuality" },
  { value: "reasoning", label: "Reasoning" },
  { value: "summarization", label: "Summarization" },
  { value: "instruction-following", label: "Instruction Following" },
  { value: "safety", label: "Safety" },
] as const;

export function normalizeCategory(category: string): string {
  if (!category) return "general";
  const trimmed = category.trim().toLowerCase();
  return trimmed
    .replace(/[^a-z0-9\s-_]/g, "")
    .replace(/[\s_]+/g, "-")
    .replace(/-+/g, "-");
}

export function formatCategory(category: string | null | undefined): string {
  if (!category) return "General";
  const normalized = normalizeCategory(category);
  const found = STANDARD_CATEGORIES.find((c) => c.value === normalized);
  if (found) return found.label;

  return normalized
    .split("-")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

export function truncate(text: string | null | undefined, max = 90): string {
  if (!text) return "";
  return text.length > max ? `${text.slice(0, max - 1)}\u2026` : text;
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
