import asyncio
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base
from app.models.dataset import Dataset, TestCase
from app.models.configuration import ModelConfiguration, Prompt, PromptVersion
from app.models.experiment import Experiment, TestCaseResult, EvaluationScore
from app.services.experiment_runner import ExperimentRunner

test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

async def live_e2e_test():
    Base.metadata.create_all(bind=test_engine)
    db = TestingSessionLocal()
    
    ds = Dataset(name="Live Groq Dataset", description="Live test")
    db.add(ds)
    db.commit()

    tc = TestCase(dataset_id=ds.id, input="What is the capital of France?", expected_output="Paris", category="factuality")
    db.add(tc)
    db.commit()

    mc = ModelConfiguration(name="Live Groq Config", provider="groq", model="llama-3.3-70b-versatile", temperature=0.0, max_tokens=256)
    db.add(mc)
    db.commit()

    pr = Prompt(name="Live Prompt", status="active")
    db.add(pr)
    db.commit()

    pv = PromptVersion(prompt_id=pr.id, version=1, system_prompt="Answer concisely.", user_template="{{input}}")
    db.add(pv)
    db.commit()

    exp = Experiment(
        name="Live Groq End-to-End Run",
        dataset_id=ds.id,
        model_config_id=mc.id,
        prompt_id=pr.id,
        prompt_version_id=pv.id,
        status="pending",
        total_cases=1,
        metrics_json=["exact_match", "contains", "semantic_similarity", "llm_judge"],
        snapshots_json={
            "dataset_name": ds.name,
            "provider": mc.provider,
            "model": mc.model,
            "temperature": mc.temperature,
            "max_tokens": mc.max_tokens,
            "prompt_name": pr.name,
            "prompt_version": pv.version,
            "system_prompt": pv.system_prompt,
            "user_template": pv.user_template,
            "concurrency": 2,
        }
    )
    db.add(exp)
    db.commit()
    exp_id = exp.id
    db.close()

    runner = ExperimentRunner()
    await runner.run_experiment(exp_id, TestingSessionLocal)

    db_read = TestingSessionLocal()
    try:
        res_exp = db_read.get(Experiment, exp_id)
        print("=== LIVE EXPERIMENT RESULTS ===")
        print("Status:", res_exp.status)
        print("Quality Score:", res_exp.quality_score)
        print("Avg Latency MS:", res_exp.avg_latency_ms)
        print("Total Tokens:", res_exp.total_tokens)
        print("Cost:", res_exp.estimated_cost)

        case_results = db_read.query(TestCaseResult).filter_by(experiment_id=exp_id).all()
        for cr in case_results:
            print("Case Model Output:", repr(cr.model_output))
            scores = db_read.query(EvaluationScore).filter_by(test_case_result_id=cr.id).all()
            for s in scores:
                print(f" - Metric {s.metric}: score={s.score}, reasoning={repr(s.reasoning)}")
    finally:
        db_read.close()

if __name__ == "__main__":
    asyncio.run(live_e2e_test())
