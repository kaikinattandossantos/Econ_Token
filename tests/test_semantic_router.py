from src.semantic_router import SemanticRoute
from src.specialist_agents import analyze_task


def test_semantic_router_vote_updates_profile(monkeypatch):
    def fake_semantic_route(task):
        return SemanticRoute(
            label="code_debugging",
            route_hint="remote",
            task_type="code_debugging",
            domain="software",
            expected_answer="bug_fix_or_explanation",
            score=0.81,
            model="fake-hf-model",
            matched_description="debug code error",
        )

    monkeypatch.setattr("src.specialist_agents.semantic_route", fake_semantic_route)
    profile = analyze_task("fix this traceback")
    assert profile.route_hint == "remote"
    assert profile.task_type == "code_debugging"
    assert profile.semantic["model"] == "fake-hf-model"