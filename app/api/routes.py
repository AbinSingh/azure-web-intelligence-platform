from fastapi import APIRouter

from app.domain.schemas import (
    UnderwritingRequest,
    UnderwritingReport,
)
from app.graph.workflow import underwriting_graph


router = APIRouter(
    prefix="/api/v1/underwriting",
    tags=["Underwriting"],
)


@router.post(
    "/research",
    response_model=UnderwritingReport,
)
async def research_property(
    request: UnderwritingRequest,
) -> UnderwritingReport:

    initial_state = {
        "account_name": request.account_name,
        "address": request.address,
        "type": request.type,
        "underwriting_questions": (
            request.underwriting_questions
        ),
    }

    result = await underwriting_graph.ainvoke(
        initial_state
    )

    return result["report"]