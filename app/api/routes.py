from fastapi import APIRouter, HTTPException
from app.core.guardrails import (
    GuardrailViolation,
    validate_underwriting_input,
)

from app.domain.schemas import UnderwritingRequest

from app.graph.workflow import(
    create_initial_state,
    underwriting_graph,
)

router = APIRouter()


@router.post("/underwrite")
async def underwrite(
    request: UnderwritingRequest,
) :
    try:
        validate_underwriting_input(
            account_name=request.account_name,
            address=request.address,
            questions=request.underwriting_questions,
        )

        initial_state = create_initial_state(
            account_name=request.account_name,
            address=request.address,
            underwriting_type=request.type,
            underwriting_questions=request.underwriting_questions,
        )

        final_state  = await underwriting_graph.ainvoke(
            initial_state
        )

        if not final_state.get("report"):
            raise HTTPException(
                status_code=503,
                detail={
                    "message": (
                        "Underwriting research could not produce usable evidence."
                    ),
                    "execution_id": final_state.get(
                        "execution_id"
                    ),
                    "errors": final_state.get(
                        "errors",
                        [],
                    ),
                },
            )

        return final_state["report"]

    except GuardrailViolation as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc