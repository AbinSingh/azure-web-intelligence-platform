import asyncio
import json
from typing import Any

from openai import OpenAI

from app.core.config import get_settings
from app.domain.schemas import Evidence


class AzureOpenAIService:
    """
    Generates evidence-grounded underwriting intelligence
    using an Azure OpenAI deployment.
    """

    def __init__(self) -> None:
        settings = get_settings()

        endpoint = settings.azure_openai_endpoint.rstrip("/")

        if endpoint.endswith("/openai/v1"):
            endpoint = endpoint[:-len("/openai/v1")].rstrip("/")

        self.client = OpenAI(
            api_key=settings.azure_openai_api_key,
            base_url=f"{endpoint}/openai/v1/",
        )

        self.model = settings.azure_openai_deployment

    async def generate_report(
        self,
        account_name: str,
        address: str,
        underwriting_type: str,
        questions: list[str],
        evidence: list[Evidence],
    ) -> dict[str, Any]:
        """
        Generate an evidence-grounded underwriting report.
        """

        evidence_payload = [
            {
                "evidence_id": item.evidence_id,
                "title": item.title,
                "url": str(item.url),
                "source": item.source,
                "content": item.content,
                "relevance": item.relevance,
                "published_date": item.published_date,
            }
            for item in evidence
        ]

        prompt = self._build_prompt(
            account_name=account_name,
            address=address,
            underwriting_type=underwriting_type,
            questions=questions,
            evidence=evidence_payload,
        )

        response = await asyncio.to_thread(
            self._generate,
            prompt,
        )

        content = response.output_text

        if not content:
            raise RuntimeError(
                "Azure OpenAI returned an empty response."
            )

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Azure OpenAI returned invalid JSON."
            ) from exc

    def _generate(self, prompt: str) -> Any:
        """
        Execute the synchronous OpenAI SDK call.
        """

        return self.client.responses.create(
            model=self.model,
            instructions=(
                "You are a factual, evidence-grounded "
                "property underwriting research analyst."
            ),
            input=prompt,
        )

    @staticmethod
    def _build_prompt(
        account_name: str,
        address: str,
        underwriting_type: str,
        questions: list[str],
        evidence: list[dict[str, Any]],
    ) -> str:
        return f"""
You are an enterprise property underwriting research analyst.

Your role is to synthesize externally collected evidence into
factual underwriting intelligence.

Account:
{account_name}

Property address:
{address}

Underwriting type:
{underwriting_type}

Underwriting questions:
{json.dumps(questions, indent=2)}

Evidence:
{json.dumps(evidence, indent=2)}

Instructions:

1. Answer every underwriting question.
2. Use only the supplied evidence.
3. Do not invent facts.
4. Clearly distinguish facts from inference.
5. Every material finding must reference one or more evidence_id values.
6. If evidence is insufficient, explicitly state that.
7. Identify information gaps.
8. Suggest additional questions only where useful.
9. Do not make the final underwriting decision.
10. Do not assign an overall accept/decline decision.
11. Do not treat absence of public information as evidence that
    an incident or hazard does not exist.
12. Return valid JSON.

Required JSON structure:

{{
  "executive_summary": "...",
  "insights": [
    {{
      "question": "...",
      "finding": "...",
      "risk_implication": "...",
      "confidence": "high|medium|low",
      "evidence_ids": ["EV-..."]
    }}
  ],
  "information_gaps": [],
  "recommended_follow_up_questions": []
}}
"""