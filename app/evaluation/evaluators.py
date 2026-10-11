from __future__ import annotations

from urllib.parse import (
    parse_qsl,
    urlencode,
    urlsplit,
    urlunsplit,
)


TRACKING_PARAMETERS = {
    "fbclid",
    "gclid",
    "ref",
}


def normalize_url(url: str) -> str:
    """Normalize URLs to reduce false mismatches."""

    parsed = urlsplit(url.strip())

    query_params = [
        (key, value)
        for key, value in parse_qsl(
            parsed.query,
            keep_blank_values=True,
        )
        if not key.lower().startswith("utm_")
        and key.lower() not in TRACKING_PARAMETERS
    ]

    path = parsed.path.rstrip("/")

    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            urlencode(sorted(query_params)),
            "",
        )
    )


def evaluate_search(
    expected_urls: list[str],
    actual_urls: list[str],
) -> dict:
    """Evaluate retrieved URLs against ground truth."""

    expected = {normalize_url(url) for url in expected_urls}
    actual = {normalize_url(url) for url in actual_urls}

    true_positives = len(expected & actual)

    precision = (
        true_positives / len(actual)
        if actual
        else 0.0
    )

    recall = (
        true_positives / len(expected)
        if expected
        else 0.0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall
        else 0.0
    )

    return {
        "expected_url_count": len(expected),
        "retrieved_url_count": len(actual),
        "matched_url_count": true_positives,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(f1, 4),
        "matched_urls": sorted(expected & actual),
        "missing_urls": sorted(expected - actual),
    }


def normalize_yes_no(answer: str) -> str:
    value = answer.strip().lower()

    if value in {"yes", "true"}:
        return "yes"

    if value in {"no", "false"}:
        return "no"

    return "invalid"


def evaluate_final_answers(
    expected_answers: list[dict],
    actual_answers: list[dict],
) -> dict:
    """Evaluate categorical underwriting answers."""

    actual_by_id = {
        item["question_id"]: item
        for item in actual_answers
    }

    total = len(expected_answers)
    correct = 0
    results = []

    for expected in expected_answers:
        question_id = expected["question_id"]
        actual = actual_by_id.get(question_id)

        expected_value = expected["expected_answer"]
        actual_value = actual.get("answer") if actual else None

        answer_type = expected["answer_type"]
        precision = recall = f1 = None

        if answer_type == "yes_no":
            expected_normalized = normalize_yes_no(
                str(expected_value)
            )

            actual_normalized = normalize_yes_no(
                str(actual_value)
            ) if actual_value is not None else "invalid"

            passed = (
                expected_normalized == actual_normalized
                and actual_normalized != "invalid"
            )

        elif answer_type == "pick_list":
            expected_set = {
                str(value).strip().lower()
                for value in expected_value
            }

            actual_set = {
                str(value).strip().lower()
                for value in (actual_value or [])
            }

            true_positives = len(expected_set & actual_set)

            precision = (
                true_positives / len(actual_set)
                if actual_set
                else 0.0
            )

            recall = (
                true_positives / len(expected_set)
                if expected_set
                else 0.0
            )

            f1 = (
                2 * precision * recall / (precision + recall)
                if precision + recall
                else 0.0
            )

            passed = expected_set == actual_set

        else:
            raise ValueError(
                f"Unsupported answer type: {answer_type}"
            )

        correct += int(passed)

        results.append({
            "question_id": question_id,
            "passed": passed,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        })

    return {
        "question_count": total,
        "correct_count": correct,
        "accuracy": round(correct / total, 4) if total else 0.0,
        "results": results,
    }