from PPT_Generator.cost_tracker import CostTracker
from PPT_Generator.llm_client import LLMClient
from PPT_Generator.models import FactQuery, Outline, SectionPlan
from PPT_Generator.planner import Planner


class FakeLLMClient:
    def __init__(self):
        self.tracker = CostTracker()

    def chat(self, system, user, response_format):
        return Outline(
            narrative_arc="arc",
            sections=[SectionPlan(section_title="Intro", pages=5, key_points=["a", "b"])],
            fact_queries=[FactQuery(entity="Imperial", attributes=["tuition"])],
        )


def test_planner_returns_outline():
    planner = Planner(FakeLLMClient())
    outline = planner.plan("topic", "brief", "audience")
    assert outline.sections[0].section_title == "Intro"
    assert outline.fact_queries[0].entity == "Imperial"
