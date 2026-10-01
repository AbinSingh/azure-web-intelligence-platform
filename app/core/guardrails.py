from collections.abc import Iterable

from app.core.config import get_settings
from app.domain.schemas import (
    Evidence,
    UnderwritingInsight,
    UnderwritingReport,
)


settings = get_settings()


class GuardrailViolation(ValueError):
    """Raised when an agent execution violates a configured guardrail."""


def validate_underwriting_input(
    *,
    account_name: str,
    address: str,
    questions: list[str],
) -> None:
    """
    Validate the initial underwriting request before research begins.
    """

    if not account_name.strip():
        raise GuardrailViolation(
            "Account name cannot be empty."
        )

    if len(account_name) > settings.max_account_name_length:
        raise GuardrailViolation(
            "Account name exceeds the configured length limit."
        )

    if not address.strip():
        raise GuardrailViolation(
            "Address cannot be empty."
        )

    if len(address) > settings.max_address_length:
        raise GuardrailViolation(
            "Address exceeds the configured length limit."
        )

    if not questions:
        raise GuardrailViolation(
            "At least one underwriting question is required."
        )

    if len(questions) > settings.max_questions:
        raise GuardrailViolation(
            f"Maximum allowed underwriting questions is "
            f"{settings.max_questions}."
        )

    for index, question in enumerate(questions):
        if not question.strip():
            raise GuardrailViolation(
                f"Underwriting question {index + 1} is empty."
            )

        if len(question) > settings.max_question_length:
            raise GuardrailViolation(
                f"Underwriting question {index + 1} exceeds "
                f"the configured length limit."
            )


def validate_search_queries(
    queries: Iterable[str],
) -> list[str]:
    """
    Validate and limit search queries before external execution.
    """

    validated_queries: list[str] = []

    for query in queries:
        normalized_query = " ".join(query.split())

        if not normalized_query:
            continue

        if len(normalized_query) > settings.max_query_length:
            normalized_query = normalized_query[
                : settings.max_query_length
            ]

        validated_queries.append(normalized_query)

    return validated_queries[: settings.max_search_queries]


def validate_evidence(
    evidence: list[Evidence],
) -> list[Evidence]:
    """
    Validate evidence before it reaches the LLM synthesis stage.
    """

    validated: list[Evidence] = []

    for item in evidence:
        if not item.content.strip():
            continue

        if len(item.content) > settings.max_content_chars_per_source:
            item = item.model_copy(
                update={
                    "content": item.content[
                        : settings.max_content_chars_per_source
                    ]
                }
            )

        validated.append(item)

    return validated[: settings.max_sources_to_scrape]


def validate_report(
    report: UnderwritingReport,
    evidence: list[Evidence],
) -> UnderwritingReport:
    """
    Validate the final LLM-generated report against collected evidence.
    """

    evidence_ids = {
        item.evidence_id
        for item in evidence
    }

    validated_insights: list[UnderwritingInsight] = []

    for insight in report.insights:
        invalid_ids = [
            evidence_id
            for evidence_id in insight.evidence_ids
            if evidence_id not in evidence_ids
        ]

        if invalid_ids:
            raise GuardrailViolation(
                "LLM generated invalid evidence references: "
                + ", ".join(invalid_ids)
            )

        validated_insights.append(insight)

    if len(report.information_gaps) > settings.max_information_gaps:
        raise GuardrailViolation(
            "Generated report contains too many information gaps."
        )

    if (
        len(report.recommended_follow_up_questions)
        > settings.max_follow_up_questions
    ):
        raise GuardrailViolation(
            "Generated report contains too many follow-up questions."
        )

    return report.model_copy(
        update={
            "insights": validated_insights,
            "evidence": evidence,
        }
    )