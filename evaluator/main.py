#!/usr/bin/env python3
"""
RAG Evaluator Application

Evaluates the RAG system using RAGAs metrics.
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from config import settings
from utils.api_client import BackendAPIClient
from evaluation.evaluator import RAGEvaluator
from reports.report_generator import ReportGenerator


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("evaluator")


def main():
    """Main entry point for the evaluator."""

    parser = argparse.ArgumentParser(
        description="Evaluate RAG system with RAGAs"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=settings.test_dataset_path,
        help="Path to test dataset (JSON)"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports",
        help="Output directory for reports"
    )

    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("RAG Evaluator - Starting Evaluation")
    logger.info("=" * 60)

    try:
        # Load test dataset
        logger.info(f"Loading test dataset from {args.dataset}")
        dataset_path = Path(args.dataset)

        if not dataset_path.exists():
            logger.error(f"Dataset not found: {dataset_path}")
            return 1

        with open(dataset_path, 'r') as f:
            test_data = json.load(f)

        logger.info(f"Loaded {len(test_data)} test questions")

        # Initialize components
        api_client = BackendAPIClient(
            base_url=settings.backend_url,
            api_prefix=settings.api_v1_prefix
        )
        evaluator = RAGEvaluator()
        report_gen = ReportGenerator(output_dir=args.output_dir)

        # Query backend for each question
        questions = []
        answers = []
        contexts = []
        ground_truths = []

        for idx, item in enumerate(test_data, 1):
            question = item["question"]
            ground_truth = item["ground_truth"]

            logger.info(f"\nQuerying {idx}/{len(test_data)}: {question[:80]}...")

            try:
                # Query backend
                response = api_client.query(question)
                data = api_client.extract_response_data(response)

                questions.append(question)
                answers.append(data["answer"])
                contexts.append(data["contexts"] if data["contexts"] else [""])
                ground_truths.append(ground_truth)

                logger.info(f"Response received with {len(data['contexts'])} contexts")

            except Exception as e:
                logger.error(f"Failed to query question {idx}: {str(e)}")
                continue

        if not questions:
            logger.error("No successful queries, cannot evaluate")
            return 1

        # Run evaluation
        logger.info("\nRunning RAGAs evaluation...")
        results = evaluator.evaluate_responses(
            questions=questions,
            answers=answers,
            contexts=contexts,
            ground_truths=ground_truths
        )

        results["total_questions"] = len(questions)

        # Generate report
        report_path = report_gen.generate_report(results)

        logger.info(f"\nReport saved to: {report_path}")
        logger.info("Evaluation complete!")

        return 0 if results.get("success") else 1

    except KeyboardInterrupt:
        logger.info("\nEvaluation interrupted by user")
        return 130

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
