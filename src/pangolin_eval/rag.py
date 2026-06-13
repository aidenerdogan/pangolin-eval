from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pangolin_eval.config import parse_models, validate_config
from pangolin_eval.models import (
    ModelTarget,
    PromptCase,
    RagDocument,
    RagQuestion,
    RagReport,
    RagResult,
)
from pangolin_eval.runner import complete_with_retries, provider_for
from pangolin_eval.scoring import estimate_cost_usd, estimate_tokens, keyword_quality_score


def load_rag_config(path: str | Path) -> dict[str, Any]:
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    validate_rag_config(data)
    return data


def validate_rag_config(data: dict[str, Any]) -> None:
    if not isinstance(data, dict):
        raise ValueError("RAG config must be a JSON object.")
    base_config = {
        "models": data.get("models"),
        "prompts": [
            {
                "id": question.get("id"),
                "messages": [{"role": "user", "content": question.get("question", "")}],
                "expected_keywords": question.get("expected_keywords", []),
            }
            for question in data.get("questions", [])
            if isinstance(question, dict)
        ],
    }
    validate_config(base_config)

    documents = data.get("documents")
    if not isinstance(documents, list) or not documents:
        raise ValueError("RAG config must include a non-empty 'documents' list.")
    document_ids: set[str] = set()
    for index, document in enumerate(documents, start=1):
        if not isinstance(document, dict):
            raise ValueError(f"RAG document {index} must be an object.")
        document_id = _require_string(document, "id", f"RAG document {index}")
        _require_string(document, "text", f"RAG document {index}")
        if document_id in document_ids:
            raise ValueError(f"RAG document id '{document_id}' must be unique.")
        document_ids.add(document_id)

    questions = data.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ValueError("RAG config must include a non-empty 'questions' list.")
    for index, question in enumerate(questions, start=1):
        _require_string(question, "id", f"RAG question {index}")
        _require_string(question, "question", f"RAG question {index}")
        context_ids = question.get("context_ids")
        if not isinstance(context_ids, list) or not context_ids:
            raise ValueError(f"RAG question {index} must include context_ids.")
        for context_id in context_ids:
            if context_id not in document_ids:
                raise ValueError(
                    f"RAG question {index} references unknown document '{context_id}'."
                )


def parse_documents(data: dict[str, Any]) -> list[RagDocument]:
    return [
        RagDocument(id=document["id"], text=document["text"])
        for document in data["documents"]
    ]


def parse_questions(data: dict[str, Any]) -> list[RagQuestion]:
    return [
        RagQuestion(
            id=question["id"],
            question=question["question"],
            context_ids=list(question["context_ids"]),
            expected_keywords=list(question.get("expected_keywords", [])),
            feature=question.get("feature"),
            workflow=question.get("workflow"),
            environment=question.get("environment"),
            prompt_version=question.get("prompt_version"),
        )
        for question in data["questions"]
    ]


def run_rag_evaluation(
    run_name: str,
    description: str,
    models: list[ModelTarget],
    documents: list[RagDocument],
    questions: list[RagQuestion],
    content_mode: str = "full",
) -> RagReport:
    document_by_id = {document.id: document for document in documents}
    results: list[RagResult] = []

    for model in models:
        provider = provider_for(model)
        for question in questions:
            context_documents = [document_by_id[doc_id] for doc_id in question.context_ids]
            context = render_context(context_documents)
            prompt = PromptCase(
                id=question.id,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Answer using only the provided context. "
                            "Cite document ids when possible."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Context:\n{context}\n\nQuestion: {question.question}",
                    },
                ],
                expected_keywords=question.expected_keywords,
                feature=question.feature,
                workflow=question.workflow,
                environment=question.environment,
                prompt_version=question.prompt_version,
            )
            completion, _, error, timed_out = complete_with_retries(provider, model, prompt)
            context_tokens = estimate_tokens(context)
            unused_context_signal = unused_context_ratio(
                context_documents,
                question.expected_keywords,
            )
            if error is not None:
                results.append(
                    RagResult(
                        question_id=question.id,
                        model_id=model.id,
                        response=None,
                        retrieved_context_tokens=context_tokens,
                        answer_tokens=0,
                        latency_ms=0,
                        estimated_cost_usd=0,
                        answer_coverage=None,
                        faithfulness_score=None,
                        context_efficiency=None,
                        unused_context_signal=unused_context_signal,
                        missing_citation=True,
                        success=False,
                        status="timeout" if timed_out else "error",
                        error=error,
                    )
                )
                continue

            answer_coverage = keyword_quality_score(
                completion.text,
                question.expected_keywords,
            )
            faithfulness = faithfulness_score(
                completion.text,
                context,
                question.expected_keywords,
            )
            context_efficiency = (
                (answer_coverage or 0) / max(context_tokens, 1) * 1000
            )
            response = None if content_mode == "metadata_only" else completion.text
            results.append(
                RagResult(
                    question_id=question.id,
                    model_id=model.id,
                    response=response,
                    retrieved_context_tokens=context_tokens,
                    answer_tokens=completion.output_tokens,
                    latency_ms=completion.latency_ms,
                    estimated_cost_usd=estimate_cost_usd(
                        completion.input_tokens,
                        completion.output_tokens,
                        model.input_price_per_1m,
                        model.output_price_per_1m,
                    ),
                    answer_coverage=answer_coverage,
                    faithfulness_score=faithfulness,
                    context_efficiency=context_efficiency,
                    unused_context_signal=unused_context_signal,
                    missing_citation=not cites_any_document(
                        completion.text,
                        question.context_ids,
                    ),
                )
            )

    return RagReport(
        run_name=run_name,
        description=description,
        results=results,
        content_mode=content_mode,
    )


def parse_rag_models(data: dict[str, Any]) -> list[ModelTarget]:
    return parse_models({"models": data["models"]})


def render_context(documents: list[RagDocument]) -> str:
    return "\n\n".join(f"[{document.id}] {document.text}" for document in documents)


def faithfulness_score(
    response: str,
    context: str,
    expected_keywords: list[str],
) -> float | None:
    if not expected_keywords:
        return None
    response_lower = response.lower()
    context_lower = context.lower()
    supported = [
        keyword
        for keyword in expected_keywords
        if keyword.lower() in response_lower and keyword.lower() in context_lower
    ]
    response_matches = [
        keyword for keyword in expected_keywords if keyword.lower() in response_lower
    ]
    if not response_matches:
        return 0
    return len(supported) / len(response_matches)


def unused_context_ratio(
    documents: list[RagDocument],
    expected_keywords: list[str],
) -> float:
    if not documents or not expected_keywords:
        return 0
    unused = 0
    for document in documents:
        text = document.text.lower()
        if not any(keyword.lower() in text for keyword in expected_keywords):
            unused += 1
    return unused / len(documents)


def cites_any_document(response: str, context_ids: list[str]) -> bool:
    response_lower = response.lower()
    return any(context_id.lower() in response_lower for context_id in context_ids)


def _require_string(data: dict[str, Any], field: str, owner: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{owner} field '{field}' must be a non-empty string.")
    return value
