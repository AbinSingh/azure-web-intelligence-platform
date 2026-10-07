from fastapi import APIRouter, HTTPException, Request
from app.core.guardrails import (
    GuardrailViolation,
    validate_underwriting_input,
)

from app.domain.schemas import UnderwritingRequest

from app.graph.workflow import(
    create_initial_state
)

router = APIRouter()


@router.post("/underwrite")
async def underwrite(
    request: UnderwritingRequest,
    http_request: Request
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

        config = {
            "configurable": {
                "thread_id": initial_state["execution_id"],
            }
        }

        graph = http_request.app.state.underwriting_graph

        final_state = await graph.ainvoke(
            initial_state,
            config=config,
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

@router.post("/underwrite/{execution_id}/resume")
async def resume_underwriting(
    execution_id: str,
    request: Request,
):
    config = {
        "configurable": {
            "thread_id": execution_id,
        }
    }

    graph = request.app.state.underwriting_graph

    final_state = await graph.ainvoke(
        None,
        config=config,
    )

    if not final_state.get("report"):
        raise HTTPException(
            status_code=503,
            detail={
                "message": (
                    "Underwriting execution did not "
                    "produce a completed report."
                ),
                "execution_id": execution_id,
                "errors": final_state.get(
                    "errors",
                    [],
                ),
            },
        )

    return final_state["report"]