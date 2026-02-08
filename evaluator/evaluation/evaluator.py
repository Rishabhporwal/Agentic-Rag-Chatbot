"""
RAG Evaluator using RAGAs metrics.
"""

import logging
from typing import List, Dict, Any
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    context_precision,
    context_recall,
    faithfulness,
    answer_relevancy
)


logger = logging.getLogger("evaluator")


class RAGEvaluator:
    """Evaluates RAG system using RAGAs metrics."""

    def __init__(self):
        """Initialize the evaluator."""
        self.metrics = [
            context_precision,
            context_recall,
            faithfulness,
            answer_relevancy
        ]
        logger.info("RAGEvaluator initialized with 4 metrics")

    def evaluate_responses(
        self,
        questions: List[str],
        answers: List[str],
        contexts: List[List[str]],
        ground_truths: List[str]
    ) -> Dict[str, Any]:
        """
        Evaluate RAG responses using RAGAs.

        Args:
            questions: List of questions
            answers: List of generated answers
            contexts: List of context lists (one list per question)
            ground_truths: List of ground truth answers

        Returns:
            Dictionary with evaluation results
        """
        logger.info(f"Evaluating {len(questions)} responses...")

        # Create dataset
        data = {
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "ground_truth": ground_truths
        }

        dataset = Dataset.from_dict(data)

        # Run evaluation
        try:
            results = evaluate(dataset, metrics=self.metrics)

            logger.info("Evaluation completed successfully")

            return {
                "success": True,
                "metrics": {
                    "context_precision": results["context_precision"],
                    "context_recall": results["context_recall"],
                    "faithfulness": results["faithfulness"],
                    "answer_relevancy": results["answer_relevancy"]
                },
                "scores": results.to_pandas().to_dict(orient="records")
            }

        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
