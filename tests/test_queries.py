from app.domain.schemas import PropertyProfile, ResearchRequest
from app.graph.nodes import build_queries


def test_query_generation() -> None:
    req = ResearchRequest(property=PropertyProfile(address="10 Example Road", occupancy="warehouse"))
    state = {"request": req}
    result = build_queries(state)
    assert any("10 Example Road" in q for q in result["queries"])
    assert any("warehouse" in q for q in result["queries"])
