import math
from collections import Counter
from typing import Any, Dict, Optional

from app.services.evaluators.base import BaseEvaluator, EvaluationInput, MetricResult

def _compute_fallback_similarity(s1: str, s2: str) -> float:
    """Fallback TF-IDF style token cosine similarity calculation without external heavy libraries."""
    words1 = [w.lower() for w in s1.split() if w.strip()]
    words2 = [w.lower() for w in s2.split() if w.strip()]
    if not words1 or not words2:
        return 100.0 if s1.strip() == s2.strip() else 0.0

    vec1 = Counter(words1)
    vec2 = Counter(words2)

    intersection = set(vec1.keys()) & set(vec2.keys())
    dot_product = sum(vec1[w] * vec2[w] for w in intersection)

    norm1 = math.sqrt(sum(val ** 2 for val in vec1.values()))
    norm2 = math.sqrt(sum(val ** 2 for val in vec2.values()))

    if norm1 == 0 or norm2 == 0:
        return 0.0

    cosine = dot_product / (norm1 * norm2)
    return round(cosine * 100.0, 2)

class SemanticSimilarityEvaluator(BaseEvaluator):
    def __init__(self, threshold: float = 75.0):
        super().__init__(threshold=threshold)

    async def evaluate(
        self, eval_input: EvaluationInput, config: Optional[Dict[str, Any]] = None
    ) -> MetricResult:
        expected = eval_input.expected_output.strip()
        actual = eval_input.model_output.strip()

        if not expected or not actual:
            score = 100.0 if expected == actual else 0.0
            return MetricResult(
                metric="semantic_similarity",
                score=score,
                passed=(score >= self.threshold),
                reasoning="Empty input/output evaluated.",
                status="success",
            )

        sim_score = 0.0
        try:
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5)).fit([expected, actual])
            tfidf_matrix = vectorizer.transform([expected, actual])
            cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            sim_score = round(float(cosine_sim) * 100.0, 2)
        except Exception:
            sim_score = _compute_fallback_similarity(expected, actual)

        # Enforce range [0.0, 100.0]
        sim_score = max(0.0, min(100.0, sim_score))
        passed = (sim_score >= self.threshold)

        reasoning = (
            f"Semantic similarity score of {sim_score:.1f}% met threshold ({self.threshold}%)."
            if passed
            else f"Semantic similarity score of {sim_score:.1f}% fell below threshold ({self.threshold}%)."
        )

        return MetricResult(
            metric="semantic_similarity",
            score=sim_score,
            passed=passed,
            reasoning=reasoning,
            status="success",
            details={"algorithm": "TF-IDF N-gram Cosine Similarity"},
        )
