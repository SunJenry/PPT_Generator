from typing import TYPE_CHECKING, Optional, Type, TypeVar

from openai import APIConnectionError, APITimeoutError, InternalServerError, OpenAI, RateLimitError
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from PPT_Generator.cost_tracker import CostTracker

if TYPE_CHECKING:
    from PPT_Generator.config import Settings

T = TypeVar("T", bound=BaseModel)

TRANSIENT_ERRORS = (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError, RuntimeError)


class LLMClient:
    def __init__(self, cost_tracker: CostTracker, settings: Optional["Settings"] = None):
        if settings is None:
            from PPT_Generator.config import settings as default_settings

            settings = default_settings

        self.client = OpenAI(api_key=settings.ark_api_key, base_url=settings.ark_base_url)
        self.model = settings.ark_model
        self.cost_tracker = cost_tracker

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(TRANSIENT_ERRORS),
        reraise=True,
    )
    def chat(self, system: str, user: str, response_format: Type[T]) -> T:
        completion = self.client.beta.chat.completions.parse(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format=response_format,
        )

        if not completion.choices:
            raise RuntimeError("LLM response contained no choices")

        message = completion.choices[0].message
        if message.refusal:
            raise RuntimeError(f"Model refused: {message.refusal}")

        if completion.usage is None:
            raise RuntimeError("LLM response missing usage information")

        self.cost_tracker.add_llm_call(completion.usage.prompt_tokens, completion.usage.completion_tokens)

        if message.parsed is None:
            raise RuntimeError("LLM did not produce valid structured output")

        return message.parsed
