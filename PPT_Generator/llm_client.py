from typing import Type, TypeVar

from openai import OpenAI
from pydantic import BaseModel

from PPT_Generator.config import settings
from PPT_Generator.cost_tracker import CostTracker

T = TypeVar("T", bound=BaseModel)


class LLMClient:
    def __init__(self, cost_tracker: CostTracker):
        self.client = OpenAI(api_key=settings.ark_api_key, base_url=settings.ark_base_url)
        self.model = settings.ark_model
        self.cost_tracker = cost_tracker

    def chat(self, system: str, user: str, response_format: Type[T]) -> T:
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format=response_format,
        )
        message = completion.choices[0].message
        if message.refusal:
            raise RuntimeError(f"Model refused: {message.refusal}")
        usage = completion.usage
        self.cost_tracker.add_llm_call(usage.prompt_tokens, usage.completion_tokens)
        return message.parsed
