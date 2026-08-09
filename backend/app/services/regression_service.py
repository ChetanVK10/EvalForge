from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

from app.models.experiment import Experiment, TestCaseResult, EvaluationScore
from app.schemas.experiment import ExperimentResponse
from app.services.experiment_runner import CASE_PASS_THRESHOLD
from app.services.experiment_service import _build_experiment_response
from app.schemas.regression import (
    CategoryRegression,
    CompareRequest,
    PromotionGate,
    PromotionGateRule,
    RegressionCase,
    RegressionComparisonResponse,
    RegressionMetric,
)
from app.services.settings_service import get_settings

CASE_CHANGE_THRESHOLD_POINTS = 10.0

METRIC_LABELS: Dict[str, str] = {
    "overall_quality": "Overall Quality",
    "factuality": "Factuality",
    "reasoning": "Reasoning",
    "completeness": "Completeness",
    "response_completeness": "Completeness",
    "instruction": "Instruction Following",
    "instruction-following": "Instruction Following",
    "exact_match": "Exact Match",
    "keyword_match": "Keyword Match",
    "semantic_similarity": "Semantic Similarity",
    "llm_judge": "LLM Judge",
}

def _round(val: float, precision: int = 1) -> float:
    return round(float(val), precision)

def _status_for_quality(delta_points: float, allowed_regression_pct: float) -> str:
    if delta_points < -allowed_regression_pct:
        return "FAIL"
    elif delta_points < -(allowed_regression_pct / 2.0):
        return "WARNING"
    return "PASS"

def _status_for_increase(delta_pct: float, allowed_increase_pct: float) -> str:
    if delta_pct > allowed_increase_pct:
        return "FAIL"
    elif delta_pct > (allowed_increase_pct / 2.0):
        return "WARNING"
    return "PASS"

def _is_case_passed(case_res: TestCaseResult) -> bool:
    if case_res.status != "completed":
        return False
    if case_res.case_quality_score is not None:
        if case_res.case_quality_score < CASE_PASS_THRESHOLD:
            return False
    if case_res.scores:
        for s in case_res.scores:
            if s.status == "success" and not s.passed:
                return False
    return True

def compare_experiments(
    db: Session,
    baseline_id: str,
    candidate_id: str,
) -> RegressionComparisonResponse:
    if baseline_id == candidate_id:
        raise ValueError("Baseline and candidate must be different experiments.")

    # Load baseline experiment with case results and scores
    stmt_base = (
        select(Experiment)
        .options(joinedload(Experiment.case_results).joinedload(TestCaseResult.scores))
        .where(Experiment.id == baseline_id)
    )
    baseline = db.scalars(stmt_base).unique().first()
    if not baseline:
        raise ValueError(f"Baseline experiment '{baseline_id}' was not found.")

    # Load candidate experiment with case results and scores
    stmt_cand = (
        select(Experiment)
        .options(joinedload(Experiment.case_results).joinedload(TestCaseResult.scores))
        .where(Experiment.id == candidate_id)
    )
    candidate = db.scalars(stmt_cand).unique().first()
    if not candidate:
        raise ValueError(f"Candidate experiment '{candidate_id}' was not found.")

    # Validate completion status
    if baseline.status != "completed":
        raise ValueError(f"Baseline experiment '{baseline_id}' is not completed (status: '{baseline.status}').")
    if candidate.status != "completed":
        raise ValueError(f"Candidate experiment '{candidate_id}' is not completed (status: '{candidate.status}').")

    # Validate dataset alignment
    if baseline.dataset_id != candidate.dataset_id:
        raise ValueError(
            f"Experiments must run on the same dataset to be compared. "
            f"Baseline dataset: '{baseline.dataset_id}', Candidate dataset: '{candidate.dataset_id}'."
        )

    # Load workspace regression thresholds
    settings_data = get_settings(db)
    thresholds = settings_data.regression_thresholds

    metrics_list: List[RegressionMetric] = []

    # 1. Overall Quality Comparison
    b_qual = baseline.quality_score or 0.0
    c_qual = candidate.quality_score or 0.0
    quality_delta = _round(c_qual - b_qual, 1)

    overall_quality_metric = RegressionMetric(
        key="overall_quality",
        label="Overall Quality",
        baseline=_round(b_qual, 1),
        candidate=_round(c_qual, 1),
        delta_pct=quality_delta,
        threshold_pct=-thresholds.max_quality_regression_pct,
        direction="higher_is_better",
        unit="percent",
        status=_status_for_quality(quality_delta, thresholds.max_quality_regression_pct),
    )
    metrics_list.append(overall_quality_metric)

    # 2. Metric-Level Comparison (ONLY for metrics present in actual experiment evaluation scores)
    def _extract_metric_scores(exp: Experiment) -> Dict[str, List[float]]:
        metric_map: Dict[str, List[float]] = {}
        for case in exp.case_results:
            for s in case.scores:
                if s.status == "success":
                    metric_map.setdefault(s.metric, []).append(s.score)
        return metric_map

    b_metric_scores = _extract_metric_scores(baseline)
    c_metric_scores = _extract_metric_scores(candidate)

    # Find common metric keys present in evaluation scores
    all_evaluated_metric_keys = sorted(list(set(b_metric_scores.keys()).union(set(c_metric_scores.keys()))))

    factuality_metric_obj: Optional[RegressionMetric] = None

    for m_key in all_evaluated_metric_keys:
        b_scores = b_metric_scores.get(m_key, [])
        c_scores = c_metric_scores.get(m_key, [])
        if not b_scores or not c_scores:
            continue

        b_avg = _round(sum(b_scores) / len(b_scores), 1)
        c_avg = _round(sum(c_scores) / len(c_scores), 1)
        m_delta = _round(c_avg - b_avg, 1)

        allowed_thresh = (
            thresholds.max_factuality_regression_pct
            if m_key == "factuality"
            else thresholds.max_quality_regression_pct
        )

        reg_metric = RegressionMetric(
            key=m_key,
            label=METRIC_LABELS.get(m_key, m_key.replace("_", " ").title()),
            baseline=b_avg,
            candidate=c_avg,
            delta_pct=m_delta,
            threshold_pct=-allowed_thresh,
            direction="higher_is_better",
            unit="percent",
            status=_status_for_quality(m_delta, allowed_thresh),
        )
        metrics_list.append(reg_metric)
        if m_key == "factuality":
            factuality_metric_obj = reg_metric

    # 3. Latency Comparison
    latency_delta_pct: Optional[float] = None
    if (
        baseline.avg_latency_ms is not None
        and candidate.avg_latency_ms is not None
        and baseline.avg_latency_ms > 0
    ):
        b_lat = float(baseline.avg_latency_ms)
        c_lat = float(candidate.avg_latency_ms)
        latency_delta_pct = _round(((c_lat - b_lat) / b_lat) * 100.0, 1)
        metrics_list.append(
            RegressionMetric(
                key="latency",
                label="Avg Latency",
                baseline=b_lat,
                candidate=c_lat,
                delta_pct=latency_delta_pct,
                threshold_pct=thresholds.max_latency_increase_pct,
                direction="lower_is_better",
                unit="ms",
                status=_status_for_increase(latency_delta_pct, thresholds.max_latency_increase_pct),
            )
        )

    # 4. Cost Comparison
    cost_delta_pct: Optional[float] = None
    if (
        baseline.estimated_cost is not None
        and candidate.estimated_cost is not None
        and baseline.estimated_cost > 0.0
    ):
        b_cost = float(baseline.estimated_cost)
        c_cost = float(candidate.estimated_cost)
        cost_delta_pct = _round(((c_cost - b_cost) / b_cost) * 100.0, 1)
        metrics_list.append(
            RegressionMetric(
                key="cost",
                label="Estimated Cost",
                baseline=_round(b_cost, 4),
                candidate=_round(c_cost, 4),
                delta_pct=cost_delta_pct,
                threshold_pct=thresholds.max_cost_increase_pct,
                direction="lower_is_better",
                unit="usd",
                status=_status_for_increase(cost_delta_pct, thresholds.max_cost_increase_pct),
            )
        )

    # 5. Category-Level Comparison
    def _extract_category_scores(exp: Experiment) -> Dict[str, Tuple[float, int]]:
        cat_groups: Dict[str, List[float]] = {}
        for case in exp.case_results:
            if case.case_quality_score is not None:
                cat_groups.setdefault(case.category or "general", []).append(case.case_quality_score)
        res: Dict[str, Tuple[float, int]] = {}
        for cat, scores in cat_groups.items():
            if scores:
                res[cat] = (_round(sum(scores) / len(scores), 1), len(scores))
        return res

    b_cat_map = _extract_category_scores(baseline)
    c_cat_map = _extract_category_scores(candidate)

    common_categories = sorted(list(set(b_cat_map.keys()).intersection(set(c_cat_map.keys()))))
    categories_list: List[CategoryRegression] = []

    for cat in common_categories:
        b_score, _ = b_cat_map[cat]
        c_score, _ = c_cat_map[cat]
        c_delta = _round(c_score - b_score, 1)
        is_critical = cat in thresholds.critical_categories
        categories_list.append(
            CategoryRegression(
                category=cat,
                baseline=b_score,
                candidate=c_score,
                delta_pct=c_delta,
                critical=is_critical,
            )
        )
    categories_list.sort(key=lambda c: c.delta_pct)

    # 6. Case-Level Alignment & Regression Identification
    # Primary alignment by test_case_id
    baseline_by_id: Dict[str, TestCaseResult] = {}
    for case in baseline.case_results:
        if case.test_case_id:
            baseline_by_id[case.test_case_id] = case

    regressed_cases: List[RegressionCase] = []
    improved_cases: List[RegressionCase] = []

    for cand_case in candidate.case_results:
        if not cand_case.test_case_id or cand_case.test_case_id not in baseline_by_id:
            # Explicit Rule 3: Test cases without exact ID match in baseline are unaligned/non-comparable
            continue

        base_case = baseline_by_id[cand_case.test_case_id]
        b_score = base_case.case_quality_score if base_case.case_quality_score is not None else 0.0
        c_score = cand_case.case_quality_score if cand_case.case_quality_score is not None else 0.0
        case_delta = _round(c_score - b_score, 1)

        base_passed = _is_case_passed(base_case)
        cand_passed = _is_case_passed(cand_case)

        # Judge explanation from score reasoning ONLY if metric is llm_judge
        judge_explanation = ""
        metric_diagnostics = []
        for s in cand_case.scores:
            m_key = (s.metric or "").strip().lower()
            if m_key == "llm_judge":
                if s.reasoning and not judge_explanation:
                    judge_explanation = s.reasoning
            elif s.reasoning:
                label = METRIC_LABELS.get(m_key, m_key.replace("_", " ").title())
                metric_diagnostics.append(f"{label}: {s.reasoning}")

        shared_case_info = {
            "case_id": cand_case.test_case_id,
            "input": cand_case.input,
            "expected_output": cand_case.expected_output,
            "category": cand_case.category or "general",
            "baseline_score": _round(b_score, 1),
            "candidate_score": _round(c_score, 1),
            "delta": case_delta,
            "baseline_output": base_case.model_output or "",
            "candidate_output": cand_case.model_output or "",
            "judge_explanation": judge_explanation,
            "metric_diagnostics": metric_diagnostics,
        }

        # Case Regression: candidate score drops by >= 10.0 OR (baseline passed and candidate failed)
        if (base_passed and not cand_passed) or case_delta <= -CASE_CHANGE_THRESHOLD_POINTS:
            failure_reason = cand_case.error or (
                f"Score fell below pass threshold ({c_score:.1f})."
                if cand_passed is False and base_passed is True
                else f"Score dropped by {abs(case_delta):.1f} points."
            )
            regressed_cases.append(
                RegressionCase(
                    **shared_case_info,
                    failure_reason=failure_reason,
                )
            )
        # Case Improvement: candidate score increases by >= 10.0 (and candidate passed)
        elif case_delta >= CASE_CHANGE_THRESHOLD_POINTS and cand_passed:
            improved_cases.append(
                RegressionCase(
                    **shared_case_info,
                    failure_reason="",
                )
            )

    regressed_cases.sort(key=lambda c: c.delta)
    improved_cases.sort(key=lambda c: c.delta, reverse=True)

    # 7. Promotion Gate Evaluation Logic
    rules: List[PromotionGateRule] = []
    reasons: List[str] = []

    # Quality Check
    quality_passed = quality_delta >= -thresholds.max_quality_regression_pct
    rules.append(
        PromotionGateRule(
            label="Overall quality regression",
            limit=f"≤ {thresholds.max_quality_regression_pct}%",
            actual=f"{quality_delta:+.1f}%",
            passed=quality_passed,
        )
    )
    if not quality_passed:
        reasons.append(
            f"Overall quality decreased {abs(quality_delta):.1f}%, exceeding the allowed regression of {thresholds.max_quality_regression_pct}%."
        )

    # Factuality Check (evaluated ONLY if factuality metric actually exists)
    if factuality_metric_obj is not None:
        fact_delta = factuality_metric_obj.delta_pct
        fact_passed = fact_delta >= -thresholds.max_factuality_regression_pct
        rules.append(
            PromotionGateRule(
                label="Factuality regression",
                limit=f"≤ {thresholds.max_factuality_regression_pct}%",
                actual=f"{fact_delta:+.1f}%",
                passed=fact_passed,
            )
        )
        if not fact_passed:
            reasons.append(
                f"Factuality decreased {abs(fact_delta):.1f}%, exceeding the allowed regression of {thresholds.max_factuality_regression_pct}%."
            )

    # Latency Check
    if latency_delta_pct is not None:
        latency_passed = latency_delta_pct <= thresholds.max_latency_increase_pct
        rules.append(
            PromotionGateRule(
                label="Latency increase",
                limit=f"≤ {thresholds.max_latency_increase_pct}%",
                actual=f"{latency_delta_pct:+.1f}%",
                passed=latency_passed,
            )
        )
        if not latency_passed:
            reasons.append(
                f"Average latency increased {latency_delta_pct:.1f}%, exceeding the allowed increase of {thresholds.max_latency_increase_pct}%."
            )

    # Cost Check
    if cost_delta_pct is not None:
        cost_passed = cost_delta_pct <= thresholds.max_cost_increase_pct
        rules.append(
            PromotionGateRule(
                label="Cost increase",
                limit=f"≤ {thresholds.max_cost_increase_pct}%",
                actual=f"{cost_delta_pct:+.1f}%",
                passed=cost_passed,
            )
        )
        if not cost_passed:
            reasons.append(
                f"Estimated cost increased {cost_delta_pct:.1f}%, exceeding the allowed increase of {thresholds.max_cost_increase_pct}%."
            )

    # Critical Categories Check (Rule 2: Applicable configured threshold, not zero tolerance)
    breaching_critical_categories: List[Tuple[CategoryRegression, float]] = []
    for cat_obj in categories_list:
        if cat_obj.critical:
            cat_allowed_thresh = (
                thresholds.max_factuality_regression_pct
                if cat_obj.category == "factuality"
                else thresholds.max_quality_regression_pct
            )
            if cat_obj.delta_pct < -cat_allowed_thresh:
                breaching_critical_categories.append((cat_obj, cat_allowed_thresh))

    critical_passed = len(breaching_critical_categories) == 0
    rules.append(
        PromotionGateRule(
            label="Critical-category regression",
            limit="0 breaching categories",
            actual=f"{len(breaching_critical_categories)} {('category' if len(breaching_critical_categories) == 1 else 'categories')}",
            passed=critical_passed,
        )
    )
    for cat_obj, allowed_thresh in breaching_critical_categories:
        reasons.append(
            f'Critical category "{cat_obj.category}" regressed {abs(cat_obj.delta_pct):.1f}% '
            f'({cat_obj.baseline:.1f}% → {cat_obj.candidate:.1f}%), exceeding allowed regression of {allowed_thresh:.1f}%.'
        )

    # Newly Failing Cases Check
    cases_passed = len(regressed_cases) == 0
    rules.append(
        PromotionGateRule(
            label="Newly failing cases",
            limit="0 cases",
            actual=f"{len(regressed_cases)} {('case' if len(regressed_cases) == 1 else 'cases')}",
            passed=cases_passed,
        )
    )
    if not cases_passed:
        reasons.append(
            f"{len(regressed_cases)} evaluation {('case' if len(regressed_cases) == 1 else 'cases')} regressed or failed in candidate run."
        )

    # Verdict Determination
    all_rules_passed = all(r.passed for r in rules)
    failing_metrics = [m for m in metrics_list if m.status == "FAIL"]
    warning_metrics = [m for m in metrics_list if m.status == "WARNING"]

    if not all_rules_passed or len(failing_metrics) > 0:
        verdict = "FAIL"
    elif len(warning_metrics) > 0:
        verdict = "WARNING"
    else:
        verdict = "PASS"

    summary = (
        f"Candidate quality decreased beyond configured threshold on {len(failing_metrics)} "
        f"{('metric' if len(failing_metrics) == 1 else 'metrics')}: {', '.join(m.label for m in failing_metrics)}."
        if verdict == "FAIL" and len(failing_metrics) > 0
        else (
            f"Promotion gate blocked due to rule failure: {reasons[0]}"
            if verdict == "FAIL" and len(reasons) > 0
            else (
                f"No metric breached its threshold, but {len(warning_metrics)} "
                f"{('metric is' if len(warning_metrics) == 1 else 'metrics are')} trending down."
                if verdict == "WARNING"
                else "Candidate holds or improves every gated metric against the baseline."
            )
        )
    )

    promotion_gate = PromotionGate(
        passed=all_rules_passed,
        rules=rules,
        reasons=reasons,
    )

    return RegressionComparisonResponse(
        baseline=_build_experiment_response(baseline),
        candidate=_build_experiment_response(candidate),
        verdict=verdict,
        summary=summary,
        metrics=metrics_list,
        categories=categories_list,
        regressed_cases=regressed_cases,
        improved_cases=improved_cases,
        promotion_gate=promotion_gate,
    )
