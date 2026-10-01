from fastapi import APIRouter

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
    initial_state = create_initial_state(
        account_name=request.account_name,
        address=request.address,
        underwriting_type=request.type,
        underwriting_questions=request.underwriting_questions,
    )

    final_state  = await underwriting_graph.ainvoke(
        initial_state
    )

    return final_state["report"]