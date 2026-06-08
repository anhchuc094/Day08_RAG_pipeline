"""RAG evaluation pipeline for the group project.

Chosen framework from the assignment: DeepEval.

The DeepEval path follows the README sample: build LLMTestCase objects from the
golden dataset, evaluate with Faithfulness, Answer Relevancy, Contextual Recall
and Contextual Precision, then compare at least two RAG configs. An offline
fallback is kept so the report can still run on machines without API access.
"""

from __future__ import annotations

import json
from pathlib import Path
from statistics import mean
from typing import Any

from group_project.rag.generator import generate_with_citation
from group_project.rag.retriever import tokenize

EVAL_DIR = Path(__file__).resolve().parent
GOLDEN_DATASET_PATH = EVAL_DIR / "golden_dataset.json"
RESULTS_PATH = EVAL_DIR / "results.md"
EVAL_TOP_K = 3

CONFIGS = {
    "hybrid_rerank": {
        "name": "Hybrid + Reranking",
        "mode": "hybrid",
        "use_reranking": True,
    },
    "dense_only": {
        "name": "Dense Only",
        "mode": "dense",
        "use_reranking": False,
    },
}


def load_golden_dataset() -> list[dict]:
    return json.loads(GOLDEN_DATASET_PATH.read_text(encoding="utf-8"))


def run_rag(question: str, *, mode: str, use_reranking: bool) -> dict:
    return generate_with_citation(
        question,
        top_k=EVAL_TOP_K,
        mode=mode,
        use_reranking=use_reranking,
    )


def build_test_cases(golden_dataset: list[dict], *, mode: str, use_reranking: bool) -> tuple[list[Any], list[dict]]:
    """Build DeepEval test cases using the assignment's sample structure."""
    from deepeval.test_case import LLMTestCase

    test_cases = []
    rows = []
    for item in golden_dataset:
        result = run_rag(item["question"], mode=mode, use_reranking=use_reranking)
        retrieval_context = [source["content"] for source in result["sources"]]
        test_cases.append(
            LLMTestCase(
                input=item["question"],
                actual_output=result["answer"],
                expected_output=item["expected_answer"],
                retrieval_context=retrieval_context,
            )
        )
        rows.append(
            {
                "id": item["id"],
                "question": item["question"],
                "answer": result["answer"],
                "sources": result["sources"],
            }
        )
    return test_cases, rows


def evaluate_with_deepeval(golden_dataset: list[dict], *, mode: str, use_reranking: bool) -> dict:
    """Evaluate with DeepEval, matching the README sample metrics."""
    from deepeval import evaluate
    from deepeval.metrics import (
        AnswerRelevancyMetric,
        ContextualPrecisionMetric,
        ContextualRecallMetric,
        FaithfulnessMetric,
    )

    test_cases, rows = build_test_cases(
        golden_dataset,
        mode=mode,
        use_reranking=use_reranking,
    )
    metrics = [
        FaithfulnessMetric(threshold=0.7),
        AnswerRelevancyMetric(threshold=0.7),
        ContextualRecallMetric(threshold=0.7),
        ContextualPrecisionMetric(threshold=0.7),
    ]
    result = evaluate(test_cases, metrics)
    scores = _extract_deepeval_scores(result, metrics)
    return {
        "framework": "deepeval",
        "scores": scores,
        "rows": rows,
        "raw_result": str(result),
    }


def _extract_deepeval_scores(result: Any, metrics: list[Any]) -> dict:
    """Best-effort extraction across DeepEval result versions."""
    names = {
        "Faithfulness": "faithfulness",
        "Answer Relevancy": "answer_relevance",
        "Contextual Recall": "context_recall",
        "Contextual Precision": "context_precision",
    }
    scores: dict[str, float] = {}

    test_results = getattr(result, "test_results", None) or getattr(result, "testResults", None)
    if test_results:
        metric_scores: dict[str, list[float]] = {key: [] for key in names.values()}
        for test_result in test_results:
            for metric_data in getattr(test_result, "metrics_data", []) or getattr(test_result, "metricsData", []):
                metric_name = getattr(metric_data, "name", "")
                score = getattr(metric_data, "score", None)
                mapped = names.get(metric_name)
                if mapped and score is not None:
                    metric_scores[mapped].append(float(score))
        for metric_name, values in metric_scores.items():
            if values:
                scores[metric_name] = round(mean(values), 3)

    for metric in metrics:
        mapped = names.get(getattr(metric, "__name__", ""), None) or names.get(getattr(metric, "name", ""), None)
        score = getattr(metric, "score", None)
        if mapped and score is not None:
            scores[mapped] = round(float(score), 3)

    for metric_name in names.values():
        scores.setdefault(metric_name, 0.0)
    scores["avg"] = round(mean(scores[name] for name in names.values()), 3)
    return scores


def _token_overlap(reference: str | list[str], candidate: str) -> float:
    if isinstance(reference, list):
        reference = " ".join(reference)
    ref_tokens = set(tokenize(reference))
    cand_tokens = set(tokenize(candidate))
    if not ref_tokens:
        return 0.0
    return len(ref_tokens & cand_tokens) / len(ref_tokens)


def _context_text(sources: list[dict]) -> str:
    return " ".join(source.get("content", "") for source in sources)


def _chunk_precision(expected_chunks: list[str], sources: list[dict]) -> float:
    if not sources:
        return 0.0
    relevant = 0
    for source in sources:
        if _token_overlap(expected_chunks, source.get("content", "")) >= 0.25:
            relevant += 1
    return relevant / len(sources)


def evaluate_case_offline(item: dict, result: dict) -> dict:
    answer = result.get("answer", "")
    sources = result.get("sources", [])
    context = _context_text(sources)
    expected_chunks = item.get("expected_chunks", item.get("expected_context", []))
    expected_answer = item.get("expected_answer", "")
    question = item.get("question", "")

    faithfulness = _token_overlap(answer, context)
    answer_relevance = 0.7 * _token_overlap(question, answer) + 0.3 * _token_overlap(expected_answer, answer)
    context_recall = _token_overlap(expected_chunks, context)
    context_precision = _chunk_precision(expected_chunks, sources)

    return {
        "id": item.get("id", ""),
        "question": question,
        "answer": answer,
        "faithfulness": round(faithfulness, 3),
        "answer_relevance": round(answer_relevance, 3),
        "context_recall": round(context_recall, 3),
        "context_precision": round(context_precision, 3),
        "avg": round(mean([faithfulness, answer_relevance, context_recall, context_precision]), 3),
    }


def evaluate_offline(golden_dataset: list[dict], *, mode: str, use_reranking: bool) -> dict:
    rows = []
    for item in golden_dataset:
        result = run_rag(item["question"], mode=mode, use_reranking=use_reranking)
        rows.append(evaluate_case_offline(item, result))

    metric_names = ["faithfulness", "answer_relevance", "context_recall", "context_precision", "avg"]
    scores = {metric: round(mean(row[metric] for row in rows), 3) for metric in metric_names}
    return {
        "framework": "offline_fallback",
        "scores": scores,
        "rows": rows,
        "raw_result": "DeepEval unavailable or failed; used deterministic offline fallback.",
    }


def run_config(config: dict, golden_dataset: list[dict], *, prefer_deepeval: bool = True) -> dict:
    if prefer_deepeval:
        try:
            result = evaluate_with_deepeval(
                golden_dataset,
                mode=config["mode"],
                use_reranking=config["use_reranking"],
            )
        except Exception as exc:
            result = evaluate_offline(
                golden_dataset,
                mode=config["mode"],
                use_reranking=config["use_reranking"],
            )
            result["raw_result"] = f"DeepEval failed: {exc}. Used offline fallback."
    else:
        result = evaluate_offline(
            golden_dataset,
            mode=config["mode"],
            use_reranking=config["use_reranking"],
        )

    return {
        "name": config["name"],
        **result,
    }


def compare_configs(golden_dataset: list[dict], *, prefer_deepeval: bool = True) -> dict:
    return {
        key: run_config(config, golden_dataset, prefer_deepeval=prefer_deepeval)
        for key, config in CONFIGS.items()
    }


def export_results(comparison: dict) -> None:
    content = ["# RAG Evaluation Results", ""]
    frameworks = sorted({config["framework"] for config in comparison.values()})
    content.append(f"Framework used: **{', '.join(frameworks)}**.")
    content.append("")
    content.append("## A/B Comparison")
    content.append("")
    content.append("| Config | Faithfulness | Answer Relevance | Context Recall | Context Precision | Average |")
    content.append("|---|---:|---:|---:|---:|---:|")
    for config in comparison.values():
        scores = config["scores"]
        content.append(
            f"| {config['name']} | {scores['faithfulness']} | {scores['answer_relevance']} | "
            f"{scores['context_recall']} | {scores['context_precision']} | {scores['avg']} |"
        )

    best = max(comparison.values(), key=lambda item: item["scores"]["avg"])
    content.extend(["", "## Best Config", "", f"Best average score: **{best['name']}**."])

    rows = comparison["hybrid_rerank"]["rows"]
    if rows and "avg" in rows[0]:
        worst = sorted(rows, key=lambda row: row["avg"])[:3]
        content.extend(["", "## Bottom 3 Questions", ""])
        content.append("| ID | Question | Avg | Main Issue |")
        content.append("|---|---|---:|---|")
        for row in worst:
            issue = "Cần bổ sung context hoặc tăng độ phủ retrieval"
            content.append(f"| {row['id']} | {row['question']} | {row['avg']} | {issue} |")
    else:
        content.extend(["", "## Bottom 3 Questions", "", "DeepEval raw results do not expose per-case averages in this environment."])

    content.extend(
        [
            "",
            "## Recommendations",
            "",
            "- DeepEval is the selected framework from the README sample.",
            "- Keep `expected_chunks` close to the wording in the real Markdown corpus.",
            "- Compare `Hybrid + Reranking` against `Dense Only` before changing retrieval defaults.",
            "- Use OpenRouter/OpenAI API keys when running DeepEval metrics that require an LLM judge.",
        ]
    )

    content.extend(["", "## Raw Notes", ""])
    for config in comparison.values():
        content.append(f"### {config['name']}")
        content.append("")
        content.append(str(config.get("raw_result", "")))
        content.append("")

    RESULTS_PATH.write_text("\n".join(content) + "\n", encoding="utf-8")


def main() -> None:
    dataset = load_golden_dataset()
    comparison = compare_configs(dataset, prefer_deepeval=True)
    export_results(comparison)
    print(f"Loaded {len(dataset)} test cases")
    print(f"Wrote {RESULTS_PATH}")


if __name__ == "__main__":
    main()
