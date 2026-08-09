import asyncio
from datetime import datetime
import time
from typing import Any, Callable, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.dataset import TestCase
from app.models.experiment import EvaluationScore, Experiment, TestCaseResult
from app.services.cache_service import cache_service
from app.services.evaluators.base import EvaluationInput
from app.services.evaluators.engine import EvaluationEngine
from app.services.providers.exceptions import LLMProviderError
from app.services.providers.gateway import ModelGateway
from app.services.providers.gemini import sanitize_error

CASE_PASS_THRESHOLD = 80.0

class ExperimentRunner:
    def __init__(
        self,
        gateway: Optional[ModelGateway] = None,
        evaluation_engine: Optional[EvaluationEngine] = None,
    ):
        self.gateway = gateway or ModelGateway()
        self.evaluation_engine = evaluation_engine or EvaluationEngine(gateway=self.gateway)

    def render_prompt(self, user_template: str, input_text: str) -> str:
        if not user_template:
            return input_text
        if "{{input}}" in user_template:
            return user_template.replace("{{input}}", input_text)
        return f"{user_template}\n\n{input_text}"

    async def run_experiment(
        self,
        experiment_id: str,
        db_factory: Callable[[], Session],
    ) -> None:
        db = db_factory()
        try:
            experiment = db.get(Experiment, experiment_id)
            if not experiment:
                return

            experiment.status = "running"
            experiment.started_at = datetime.utcnow()
            db.commit()

            # Load dataset test cases
            test_cases = db.scalars(
                select(TestCase).where(TestCase.dataset_id == experiment.dataset_id)
            ).all()

            experiment.total_cases = len(test_cases)
            db.commit()

            if len(test_cases) == 0:
                experiment.status = "completed"
                experiment.completed_at = datetime.utcnow()
                db.commit()
                return

            # Extract configuration snapshots
            snapshots = experiment.snapshots_json or {}
            system_prompt = snapshots.get("system_prompt", "")
            user_template = snapshots.get("user_template", "{{input}}")
            provider = snapshots.get("provider", "groq")
            model = snapshots.get("model", "llama-3.3-70b-versatile")
            temperature = snapshots.get("temperature", 0.2)
            max_tokens = snapshots.get("max_tokens", 1024)
            metrics = experiment.metrics_json or ["exact_match"]

            concurrency = int(snapshots.get("concurrency", 5))
            # Gemini concurrency is restricted to 1 to reduce request bursts.
            # Free-tier quota enforcement remains provider-side, and HTTP 429 is handled explicitly.
            if (provider or "").strip().lower() == "gemini":
                concurrency = min(concurrency, 1)

            semaphore = asyncio.Semaphore(max(1, min(20, concurrency)))

            async def process_case(case: TestCase):
                async with semaphore:
                    rendered_user = self.render_prompt(user_template, case.input)
                    
                    try:
                        llm_res = await self.gateway.generate(
                            provider=provider,
                            model=model,
                            system_prompt=system_prompt,
                            user_prompt=rendered_user,
                            temperature=temperature,
                            max_tokens=max_tokens,
                        )

                        # Evaluate LLM output
                        eval_input = EvaluationInput(
                            input=rendered_user,
                            expected_output=case.expected_output,
                            model_output=llm_res.text,
                            category=case.category,
                        )
                        eval_output = await self.evaluation_engine.evaluate(
                            eval_input, metrics=metrics
                        )

                        return {
                            "case_id": case.id,
                            "input": case.input,
                            "expected_output": case.expected_output,
                            "category": case.category,
                            "status": "completed",
                            "error": None,
                            "model_output": llm_res.text,
                            "provider": provider,
                            "model": model,
                            "latency_ms": llm_res.latency_ms,
                            "input_tokens": llm_res.input_tokens,
                            "output_tokens": llm_res.output_tokens,
                            "total_tokens": llm_res.total_tokens,
                            "estimated_cost": llm_res.estimated_cost,
                            "case_quality_score": eval_output.aggregate_score,
                            "scores": eval_output.results,
                        }
                    except LLMProviderError as e:
                        safe_err = sanitize_error(e.message)
                        return {
                            "case_id": case.id,
                            "input": case.input,
                            "expected_output": case.expected_output,
                            "category": case.category,
                            "status": "failed",
                            "error": f"Execution failed\nProvider: {provider}\nModel: {model}\nProvider error: {safe_err}",
                            "model_output": "",
                            "provider": provider,
                            "model": model,
                            "latency_ms": 0,
                            "input_tokens": None,
                            "output_tokens": None,
                            "total_tokens": None,
                            "estimated_cost": 0.0,
                            "case_quality_score": None,
                            "scores": [],
                        }
                    except Exception as e:
                        safe_err = sanitize_error(str(e))
                        return {
                            "case_id": case.id,
                            "input": case.input,
                            "expected_output": case.expected_output,
                            "category": case.category,
                            "status": "failed",
                            "error": f"Execution failed\nProvider: {provider}\nModel: {model}\nExecution error: {safe_err}",
                            "model_output": "",
                            "provider": provider,
                            "model": model,
                            "latency_ms": 0,
                            "input_tokens": None,
                            "output_tokens": None,
                            "total_tokens": None,
                            "estimated_cost": 0.0,
                            "case_quality_score": None,
                            "scores": [],
                        }

            # Gather all test case executions concurrently
            case_results_data = await asyncio.gather(
                *[process_case(tc) for tc in test_cases]
            )

            # Persist results in DB
            completed_cnt = 0
            failed_cnt = 0

            for res in case_results_data:
                if res["status"] == "completed":
                    completed_cnt += 1
                else:
                    failed_cnt += 1

                tc_result = TestCaseResult(
                    experiment_id=experiment_id,
                    test_case_id=res["case_id"],
                    input=res["input"],
                    expected_output=res["expected_output"],
                    model_output=res["model_output"],
                    category=res["category"],
                    status=res["status"],
                    error=res["error"],
                    provider=res["provider"],
                    model=res["model"],
                    latency_ms=res["latency_ms"],
                    input_tokens=res["input_tokens"],
                    output_tokens=res["output_tokens"],
                    total_tokens=res["total_tokens"],
                    estimated_cost=res["estimated_cost"],
                    case_quality_score=res["case_quality_score"],
                )
                db.add(tc_result)
                db.flush()

                for metric_res in res["scores"]:
                    eval_score = EvaluationScore(
                        test_case_result_id=tc_result.id,
                        metric=metric_res.metric,
                        score=metric_res.score,
                        passed=metric_res.passed,
                        reasoning=metric_res.reasoning,
                        status=metric_res.status,
                        error=metric_res.error,
                        details_json=metric_res.details or {},
                    )
                    db.add(eval_score)

            experiment.completed_cases = completed_cnt
            experiment.failed_cases = failed_cnt

            # Calculate experiment aggregates
            all_case_results = db.scalars(
                select(TestCaseResult).where(TestCaseResult.experiment_id == experiment_id)
            ).all()

            valid_scores = [r.case_quality_score for r in all_case_results if r.case_quality_score is not None]
            if valid_scores:
                experiment.quality_score = round(sum(valid_scores) / len(valid_scores), 1)
                passed_cases = sum(1 for s in valid_scores if s >= CASE_PASS_THRESHOLD)
                experiment.pass_rate = round((passed_cases / len(valid_scores)) * 100.0, 1)

            latencies = [r.latency_ms for r in all_case_results if r.status == "completed"]
            if latencies:
                experiment.avg_latency_ms = int(sum(latencies) / len(latencies))
                latencies_sorted = sorted(latencies)
                p95_idx = int(len(latencies_sorted) * 0.95)
                experiment.p95_latency_ms = latencies_sorted[min(p95_idx, len(latencies_sorted) - 1)]

            experiment.total_input_tokens = sum(r.input_tokens or 0 for r in all_case_results)
            experiment.total_output_tokens = sum(r.output_tokens or 0 for r in all_case_results)
            experiment.total_tokens = sum(r.total_tokens or 0 for r in all_case_results)

            completed_cases_list = [r for r in all_case_results if r.status == "completed"]
            case_costs = [r.estimated_cost for r in completed_cases_list if r.estimated_cost is not None]
            if completed_cases_list and len(case_costs) == len(completed_cases_list):
                experiment.estimated_cost = round(sum(case_costs), 6)
            else:
                experiment.estimated_cost = None

            experiment.status = "completed" if (completed_cnt > 0 or len(test_cases) == 0) else "failed"
            experiment.completed_at = datetime.utcnow()
            db.commit()
            cache_service.delete("dashboard:summary:v1")

        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("Experiment runner failed for %s: %s", experiment_id, e)
            try:
                exp = db.get(Experiment, experiment_id)
                if exp:
                    exp.status = "failed"
                    exp.completed_at = datetime.utcnow()
                    db.commit()
                    cache_service.delete("dashboard:summary:v1")
            except Exception:
                pass
        finally:
            db.close()
