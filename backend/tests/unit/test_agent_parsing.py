import pytest
from research_mesh.agents.parsing import parse_agent_response
from research_mesh.agents.schemas import ResearchPlan


def test_parse_agent_response_parses_a_valid_plan() -> None:
    plan = parse_agent_response(
        '{"search_queries": ["coral bleaching causes", "ocean temperature rise"]}',
        ResearchPlan,
    )

    assert plan.search_queries == ["coral bleaching causes", "ocean temperature rise"]


def test_parse_agent_response_rejects_invalid_json() -> None:
    with pytest.raises(ValueError, match="not valid JSON"):
        parse_agent_response("not json at all", ResearchPlan)


def test_parse_agent_response_rejects_schema_violations() -> None:
    with pytest.raises(ValueError, match="did not match the expected schema"):
        parse_agent_response('{"search_queries": []}', ResearchPlan)
