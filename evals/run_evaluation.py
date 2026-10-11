from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

# Ensure the project root is importable when this script is
# executed using: python evals/run_evaluation.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.evaluation.evaluators import (
    evaluate_final_answers,
    evaluate_search,
)
from app.evaluation.scrape_judge import evaluate_scraped_facts


EVAL_DIR = PROJECT_ROOT / "evals"
DATASET_PATH = EVAL_DIR / "datasets" / "underwriting_cases.json"
INPUTS_PATH = EVAL_DIR / "results" / "evaluation_inputs.json"
REPORT_PATH = EVAL_DIR / "results" / "evaluation_report.json"

logger = logging.getLogger(__name__)


def load_json(path: Path) -> Any:
    """Load JSON data from a file."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def evaluate_case(
    ground_truth: dict[str, Any],
    actual: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate search, scraping, and final answers for one case."""

    case_id = ground_truth["case_id"]

    logger.info("Evaluating case: %s", case_id)

    # 1. Search evaluation
    search_result = evaluate_search(
        expected_urls=ground_truth["search_ground_truth_urls"],
        actual_urls=actual.get("search_returned_urls", []),
    )

    # 2. Scrape evaluation
    actual_scrapes = {
        item["url"]: item
        for item in actual.get("scrape_results", [])
    }

    scrape_results = []

    for expected_scrape in ground_truth["scrape_ground_truth"]:
        url = expected_scrape["url"]
        scraped = actual_scrapes.get(url)

        if scraped is None:
            content = ""
            error = "No scrape result available for the expected URL."
        else:
            content = scraped.get("extracted_content", "")
            error = None

        try:
            result = evaluate_scraped_facts(
                expected_facts=expected_scrape["expected_facts"],
                extracted_content=content,
            )

            if error:
                result["error"] = error

        except Exception as exc:
            logger.exception(
                "Scrape evaluation failed for case %s, URL %s",
                case_id,
                url,
            )

            result = {
                "total_facts": len(expected_scrape["expected_facts"]),
                "supported_facts": 0,
                "pass_rate": 0.0,
                "results": [],
                "error": f"Evaluation failed: {type(exc).__name__}",
            }

        result["url"] = url
        scrape_results.append(result)

    total_facts = sum(
        result["total_facts"]
        for result in scrape_results
    )

    supported_facts = sum(
        result["supported_facts"]
        for result in scrape_results
    )

    scrape_summary = {
        "total_sources": len(scrape_results),
        "total_facts": total_facts,
        "supported_facts": supported_facts,
        "pass_rate": (
            round(supported_facts / total_facts, 4)
            if total_facts
            else 0.0
        ),
        "results": scrape_results,
    }

    # 3. Final-output evaluation
    final_result = evaluate_final_answers(
        expected_answers=ground_truth["questions"],
        actual_answers=actual.get("actual_answers", []),
    )

    # Do not count a case as passing if a scrape evaluation failed.
    scrape_evaluation_errors = sum(
        "error" in result
        for result in scrape_results
    )

    case_passed = (
        search_result["recall"] == 1.0
        and final_result["accuracy"] == 1.0
        and scrape_evaluation_errors == 0
        and scrape_summary["pass_rate"] == 1.0
    )

    return {
        "case_id": case_id,
        "passed": case_passed,
        "search": search_result,
        "scrape": scrape_summary,
        "final_output": final_result,
    }


def main() -> int:
    """Run evaluations and save the consolidated report."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    try:
        dataset = load_json(DATASET_PATH)
        actual_inputs = load_json(INPUTS_PATH)

        actual_by_id = {
            item["case_id"]: item
            for item in actual_inputs
        }

        case_results = []

        for ground_truth in dataset:
            case_id = ground_truth["case_id"]
            actual = actual_by_id.get(case_id)

            if actual is None:
                logger.error(
                    "Missing evaluation input for case %s",
                    case_id,
                )

                case_results.append({
                    "case_id": case_id,
                    "passed": False,
                    "error": "Missing evaluation input.",
                })
                continue

            case_results.append(
                evaluate_case(ground_truth, actual)
            )

        passed_cases = sum(
            result["passed"]
            for result in case_results
        )

        report = {
            "dataset": str(DATASET_PATH.relative_to(PROJECT_ROOT)),
            "total_cases": len(case_results),
            "passed_cases": passed_cases,
            "failed_cases": len(case_results) - passed_cases,
            "pass_rate": (
                round(passed_cases / len(case_results), 4)
                if case_results
                else 0.0
            ),
            "results": case_results,
        }

        REPORT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with REPORT_PATH.open("w", encoding="utf-8") as file:
            json.dump(
                report,
                file,
                indent=2,
                ensure_ascii=False,
            )

        print(json.dumps({
            "total_cases": report["total_cases"],
            "passed_cases": report["passed_cases"],
            "failed_cases": report["failed_cases"],
            "pass_rate": report["pass_rate"],
            "report_path": str(REPORT_PATH),
        }, indent=2))

        return 0 if report["failed_cases"] == 0 else 1

    except Exception:
        logger.exception("Evaluation run failed.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
