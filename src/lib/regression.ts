import type {
  CategoryRegression,
  EvaluationCategory,
  Experiment,
  EvaluationCaseResult,
  MetricResult,
  PromotionGate,
  PromotionGateRule,
  RegressionCase,
  RegressionComparison,
  RegressionMetric,
  RegressionStatus,
  RegressionThresholds,
} from "@/types";

const round = (n: number, p = 1) => Number(n.toFixed(p));

function statusFor(delta: number, threshold: number): RegressionStatus {
  if (delta < -threshold) return "FAIL";
  if (delta < -threshold / 2) return "WARNING";
  return "PASS";
}

function statusForCost(deltaPct: number, threshold: number): RegressionStatus {
  if (deltaPct > threshold) return "FAIL";
  if (deltaPct > threshold / 2) return "WARNING";
  return "PASS";
}

function findMetric(list: MetricResult[], key: string): number | undefined {
  return list.find((m) => m.key === key)?.score;
}

export interface ComparisonInput {
  baseline: Experiment;
  candidate: Experiment;
  baselineBreakdown: MetricResult[];
  candidateBreakdown: MetricResult[];
  baselineCategories: Partial<Record<EvaluationCategory, number>>;
  candidateCategories: Partial<Record<EvaluationCategory, number>>;
  baselineCases: EvaluationCaseResult[];
  candidateCases: EvaluationCaseResult[];
  thresholds: RegressionThresholds;
}

export function computeComparison(input: ComparisonInput): RegressionComparison {
  const { baseline, candidate, thresholds } = input;

  const metrics: RegressionMetric[] = [];

  const qualityDelta = round(candidate.quality_score - baseline.quality_score, 1);
  metrics.push({
    key: "overall_quality",
    label: "Overall Quality",
    baseline: baseline.quality_score,
    candidate: candidate.quality_score,
    delta_pct: qualityDelta,
    threshold_pct: -thresholds.max_quality_regression_pct,
    direction: "higher_is_better",
    unit: "percent",
    status: statusFor(qualityDelta, thresholds.max_quality_regression_pct),
  });

  const qualityMetricKeys: { key: string; label: string; threshold: number }[] = [
    { key: "factuality", label: "Factuality", threshold: thresholds.max_factuality_regression_pct },
    { key: "reasoning", label: "Reasoning", threshold: thresholds.max_factuality_regression_pct },
    {
      key: "completeness",
      label: "Completeness",
      threshold: thresholds.max_factuality_regression_pct,
    },
    {
      key: "instruction",
      label: "Instruction Following",
      threshold: thresholds.max_factuality_regression_pct,
    },
  ];

  for (const m of qualityMetricKeys) {
    const b = findMetric(input.baselineBreakdown, m.key);
    const c = findMetric(input.candidateBreakdown, m.key);
    if (b === undefined || c === undefined) continue;
    const delta = round(c - b, 1);
    metrics.push({
      key: m.key,
      label: m.label,
      baseline: b,
      candidate: c,
      delta_pct: delta,
      threshold_pct: -m.threshold,
      direction: "higher_is_better",
      unit: "percent",
      status: statusFor(delta, m.threshold),
    });
  }

  const latencyDelta = round(
    ((candidate.avg_latency_ms - baseline.avg_latency_ms) / baseline.avg_latency_ms) * 100,
    1,
  );
  metrics.push({
    key: "latency",
    label: "Avg Latency",
    baseline: baseline.avg_latency_ms,
    candidate: candidate.avg_latency_ms,
    delta_pct: latencyDelta,
    threshold_pct: thresholds.max_latency_increase_pct,
    direction: "lower_is_better",
    unit: "ms",
    status: statusForCost(latencyDelta, thresholds.max_latency_increase_pct),
  });

  const costDelta = round(
    ((candidate.estimated_cost - baseline.estimated_cost) / baseline.estimated_cost) * 100,
    1,
  );
  metrics.push({
    key: "cost",
    label: "Estimated Cost",
    baseline: baseline.estimated_cost,
    candidate: candidate.estimated_cost,
    delta_pct: costDelta,
    threshold_pct: thresholds.max_cost_increase_pct,
    direction: "lower_is_better",
    unit: "usd",
    status: statusForCost(costDelta, thresholds.max_cost_increase_pct),
  });

  const categories: CategoryRegression[] = Object.keys(input.baselineCategories)
    .filter((k) => input.candidateCategories[k as EvaluationCategory] !== undefined)
    .map((k) => {
      const category = k as EvaluationCategory;
      const b = input.baselineCategories[category]!;
      const c = input.candidateCategories[category]!;
      return {
        category,
        baseline: b,
        candidate: c,
        delta_pct: round(c - b, 1),
        critical: thresholds.critical_categories.includes(category),
      };
    })
    .sort((a, b) => a.delta_pct - b.delta_pct);

  const baselineByCase = new Map(input.baselineCases.map((c) => [c.case_id, c]));

  const regressed_cases: RegressionCase[] = [];
  const improved_cases: RegressionCase[] = [];

  for (const cand of input.candidateCases) {
    const base = baselineByCase.get(cand.case_id);
    if (!base) continue;
    const delta = round(cand.score - base.score, 1);
    const shared = {
      case_id: cand.case_id,
      input: cand.input,
      expected_output: cand.expected_output,
      category: cand.category,
      baseline_score: base.score,
      candidate_score: cand.score,
      delta,
      baseline_output: base.model_output,
      candidate_output: cand.model_output,
    };
    if (base.status === "PASS" && cand.status === "FAIL") {
      regressed_cases.push({
        ...shared,
        failure_reason: cand.failure_reason ?? "Score fell below the pass threshold.",
        judge_explanation: cand.judge_explanation,
      });
    } else if (delta >= 8 && cand.status === "PASS") {
      improved_cases.push({
        ...shared,
        failure_reason: "",
        judge_explanation: cand.judge_explanation,
      });
    }
  }

  regressed_cases.sort((a, b) => a.delta - b.delta);
  improved_cases.sort((a, b) => b.delta - a.delta);

  const factuality = metrics.find((m) => m.key === "factuality");
  const criticalRegressions = categories.filter((c) => c.critical && c.delta_pct < 0);

  const rules: PromotionGateRule[] = [
    {
      label: "Overall quality regression",
      limit: `≤ ${thresholds.max_quality_regression_pct}%`,
      actual: `${qualityDelta >= 0 ? "+" : ""}${qualityDelta}%`,
      passed: qualityDelta >= -thresholds.max_quality_regression_pct,
    },
    {
      label: "Factuality regression",
      limit: `≤ ${thresholds.max_factuality_regression_pct}%`,
      actual: factuality
        ? `${factuality.delta_pct >= 0 ? "+" : ""}${factuality.delta_pct}%`
        : "n/a",
      passed: factuality ? factuality.delta_pct >= -thresholds.max_factuality_regression_pct : true,
    },
    {
      label: "Latency increase",
      limit: `≤ ${thresholds.max_latency_increase_pct}%`,
      actual: `${latencyDelta >= 0 ? "+" : ""}${latencyDelta}%`,
      passed: latencyDelta <= thresholds.max_latency_increase_pct,
    },
    {
      label: "Cost increase",
      limit: `≤ ${thresholds.max_cost_increase_pct}%`,
      actual: `${costDelta >= 0 ? "+" : ""}${costDelta}%`,
      passed: costDelta <= thresholds.max_cost_increase_pct,
    },
    {
      label: "Critical-category regression",
      limit: "0 categories",
      actual: `${criticalRegressions.length} ${criticalRegressions.length === 1 ? "category" : "categories"}`,
      passed: criticalRegressions.length === 0,
    },
    {
      label: "Newly failing cases",
      limit: "0 cases",
      actual: `${regressed_cases.length} ${regressed_cases.length === 1 ? "case" : "cases"}`,
      passed: regressed_cases.length === 0,
    },
  ];

  const reasons: string[] = [];
  if (qualityDelta < -thresholds.max_quality_regression_pct) {
    reasons.push(
      `Overall quality decreased ${Math.abs(qualityDelta)}%, exceeding the allowed regression of ${thresholds.max_quality_regression_pct}%.`,
    );
  }
  if (factuality && factuality.delta_pct < -thresholds.max_factuality_regression_pct) {
    reasons.push(
      `Factuality decreased ${Math.abs(factuality.delta_pct)}%, exceeding the allowed regression of ${thresholds.max_factuality_regression_pct}%.`,
    );
  }
  if (latencyDelta > thresholds.max_latency_increase_pct) {
    reasons.push(
      `Average latency increased ${latencyDelta}%, exceeding the allowed increase of ${thresholds.max_latency_increase_pct}%.`,
    );
  }
  if (costDelta > thresholds.max_cost_increase_pct) {
    reasons.push(
      `Estimated cost increased ${costDelta}%, exceeding the allowed increase of ${thresholds.max_cost_increase_pct}%.`,
    );
  }
  for (const c of criticalRegressions) {
    reasons.push(
      `Critical category "${c.category}" regressed ${Math.abs(c.delta_pct)}% (${c.baseline}% → ${c.candidate}%).`,
    );
  }
  if (regressed_cases.length > 0) {
    reasons.push(
      `${regressed_cases.length} previously passing evaluation ${regressed_cases.length === 1 ? "case" : "cases"} now fail.`,
    );
  }

  const failing = metrics.filter((m) => m.status === "FAIL");
  const warning = metrics.filter((m) => m.status === "WARNING");
  const verdict: RegressionStatus =
    failing.length > 0 ? "FAIL" : warning.length > 0 ? "WARNING" : "PASS";

  const summary =
    verdict === "FAIL"
      ? `Candidate quality decreased beyond the configured threshold on ${failing.length} ${failing.length === 1 ? "metric" : "metrics"}: ${failing.map((m) => m.label).join(", ")}.`
      : verdict === "WARNING"
        ? `No metric breached its threshold, but ${warning.length} ${warning.length === 1 ? "metric is" : "metrics are"} trending down.`
        : "Candidate holds or improves every gated metric against the baseline.";

  const gate: PromotionGate = {
    passed: rules.every((r) => r.passed),
    rules,
    reasons,
  };

  return {
    baseline,
    candidate,
    verdict,
    summary,
    metrics,
    categories,
    regressed_cases,
    improved_cases,
    promotion_gate: gate,
  };
}
