"""
Report Generator for evaluation results.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


logger = logging.getLogger("evaluator.report")


class ReportGenerator:
    """Generates evaluation reports."""

    def __init__(self, output_dir: str = "reports"):
        """
        Initialize report generator.

        Args:
            output_dir: Directory for output files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        logger.info(f"ReportGenerator initialized (output_dir={output_dir})")

    def generate_report(self, results: Dict[str, Any]) -> str:
        """
        Generate evaluation report.

        Args:
            results: Evaluation results dictionary

        Returns:
            Path to generated report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.output_dir / f"evaluation_report_{timestamp}.json"

        # Add timestamp to results
        results["timestamp"] = datetime.now().isoformat()
        results["report_version"] = "1.0"

        # Write JSON report
        with open(report_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Report generated: {report_path}")

        # Print summary
        self._print_summary(results)

        return str(report_path)

    def _print_summary(self, results: Dict[str, Any]):
        """Print evaluation summary."""
        if not results.get("success"):
            print("\n❌ Evaluation failed:", results.get("error"))
            return

        metrics = results.get("metrics", {})

        print("\n" + "=" * 60)
        print("RAG Evaluation Report")
        print("=" * 60)
        print(f"\nTimestamp: {results.get('timestamp')}")
        print(f"Questions evaluated: {results.get('total_questions', 'N/A')}")
        print("\nMetrics:")
        print(f"  Context Precision: {metrics.get('context_precision', 0):.4f}")
        print(f"  Context Recall:    {metrics.get('context_recall', 0):.4f}")
        print(f"  Faithfulness:      {metrics.get('faithfulness', 0):.4f}")
        print(f"  Answer Relevancy:  {metrics.get('answer_relevancy', 0):.4f}")
        print("=" * 60)
