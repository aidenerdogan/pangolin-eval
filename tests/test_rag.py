from __future__ import annotations

import unittest

from pangolin_eval.models import ModelTarget, RagDocument, RagQuestion
from pangolin_eval.rag import (
    cites_any_document,
    faithfulness_score,
    repeated_context_ratio,
    run_rag_evaluation,
    unused_context_ratio,
    validate_rag_config,
)


class RagTest(unittest.TestCase):
    def test_rag_evaluation_computes_context_metrics(self) -> None:
        report = run_rag_evaluation(
            run_name="rag",
            description="",
            models=[
                ModelTarget(
                    id="mock-model",
                    provider="mock",
                    input_price_per_1m=0.1,
                    output_price_per_1m=0.2,
                    mock_response="Refunds are available within 30 days in [doc-1].",
                    mock_latency_ms=100,
                )
            ],
            documents=[
                RagDocument(
                    id="doc-1",
                    text="Refunds are available within 30 days for damaged items.",
                )
            ],
            questions=[
                RagQuestion(
                    id="case-1",
                    question="What is the refund window?",
                    context_ids=["doc-1"],
                    expected_keywords=["refund", "30 days"],
                )
            ],
            max_context_tokens=1,
        )

        result = report.results[0]

        self.assertEqual(report.schema_version, "pangolin-eval.rag_report.v1")
        self.assertTrue(result.success)
        self.assertEqual(result.answer_coverage, 1.0)
        self.assertEqual(result.faithfulness_score, 1.0)
        self.assertGreater(result.context_efficiency or 0, 0)
        self.assertFalse(result.missing_citation)
        self.assertTrue(result.oversized_context)
        self.assertIsNotNone(result.cost_per_covered_answer_usd)

    def test_rag_evaluation_rejects_invalid_content_mode(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported content mode"):
            run_rag_evaluation(
                run_name="rag",
                description="",
                models=[
                    ModelTarget(
                        id="mock-model",
                        provider="mock",
                        input_price_per_1m=0.1,
                        output_price_per_1m=0.2,
                    )
                ],
                documents=[RagDocument(id="doc-1", text="Refund policy.")],
                questions=[
                    RagQuestion(
                        id="case-1",
                        question="What is the policy?",
                        context_ids=["doc-1"],
                    )
                ],
                content_mode="metadata-only",
            )

    def test_validate_rag_config_rejects_non_object_question(self) -> None:
        with self.assertRaisesRegex(ValueError, "RAG question 1 must be an object"):
            validate_rag_config(
                {
                    "models": [
                        {
                            "id": "mock-model",
                            "provider": "mock",
                            "input_price_per_1m": 0.1,
                            "output_price_per_1m": 0.2,
                        }
                    ],
                    "documents": [{"id": "doc-1", "text": "Refund policy."}],
                    "questions": ["not-an-object"],
                }
            )

    def test_validate_rag_config_rejects_non_string_context_id(self) -> None:
        with self.assertRaisesRegex(ValueError, "context_ids must contain only strings"):
            validate_rag_config(
                {
                    "models": [
                        {
                            "id": "mock-model",
                            "provider": "mock",
                            "input_price_per_1m": 0.1,
                            "output_price_per_1m": 0.2,
                        }
                    ],
                    "documents": [{"id": "doc-1", "text": "Refund policy."}],
                    "questions": [
                        {
                            "id": "case-1",
                            "question": "What is the policy?",
                            "context_ids": [123],
                        }
                    ],
                }
            )

    def test_rag_helpers_flag_missing_citation_and_unused_context(self) -> None:
        self.assertTrue(cites_any_document("Use [doc-1].", ["doc-1"]))
        self.assertFalse(cites_any_document("No citation.", ["doc-1"]))
        self.assertEqual(
            faithfulness_score("refund 30 days", "refund 30 days", ["refund"]),
            1.0,
        )
        self.assertEqual(
            unused_context_ratio(
                [
                    RagDocument(id="doc-1", text="refund policy"),
                    RagDocument(id="doc-2", text="unrelated billing"),
                ],
                ["refund"],
            ),
            0.5,
        )
        self.assertEqual(
            repeated_context_ratio(
                [
                    RagDocument(id="doc-1", text="same sentence. unique"),
                    RagDocument(id="doc-2", text="same sentence. different"),
                ]
            ),
            0.25,
        )


if __name__ == "__main__":
    unittest.main()
