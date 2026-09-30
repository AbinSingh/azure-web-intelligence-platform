from app.domain.schemas import PropertyProfile, ResearchRequest


def test_request_defaults() -> None:
    request = ResearchRequest(property=PropertyProfile(address="10 Example Road"))
    assert len(request.underwriting_questions) == 10
