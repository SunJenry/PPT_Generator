from PPT_Generator.llm_client import LLMClient
from PPT_Generator.models import Outline


PLANNER_SYSTEM = """You are a presentation planner. Given a topic, brief, and audience, produce:
1. A narrative arc for a 25-30 slide presentation
2. A list of sections, each with an estimated page count and key points
3. A list of fact queries that must be verified via web search

Output must follow the provided JSON schema."""

PLANNER_USER_TEMPLATE = """Topic: {topic}
Brief: {brief}
Audience: {audience}

Create a cohesive outline for a 25-30 slide presentation."""


class Planner:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def plan(self, topic: str, brief: str, audience: str) -> Outline:
        user_prompt = PLANNER_USER_TEMPLATE.format(topic=topic, brief=brief, audience=audience)
        return self.llm_client.chat(PLANNER_SYSTEM, user_prompt, Outline)
