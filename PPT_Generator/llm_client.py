import json
import re
from typing import TYPE_CHECKING, Optional, Type, TypeVar

from openai import APIConnectionError, APITimeoutError, InternalServerError, OpenAI, RateLimitError
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from PPT_Generator.cost_tracker import CostTracker

if TYPE_CHECKING:
    from PPT_Generator.config import Settings

T = TypeVar("T", bound=BaseModel)

TRANSIENT_ERRORS = (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError, RuntimeError)

_FENCE_RE = re.compile(r"^```[a-zA-Z]*\s*|\s*```$")


def _extract_json(content: str) -> str:
    """Extract a JSON payload from LLM output, stripping Markdown code fences if present."""
    text = content.strip()
    if text.startswith("```"):
        text = _FENCE_RE.sub("", text).strip()
    return text


class LLMClient:
    def __init__(self, cost_tracker: CostTracker, settings: Optional["Settings"] = None):
        if settings is None:
            from PPT_Generator.config import settings as default_settings

            settings = default_settings

        self.client = OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
        self.model = settings.deepseek_model
        self.cost_tracker = cost_tracker

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(TRANSIENT_ERRORS),
        reraise=True,
    )
    def chat(
        self,
        system: str,
        user: str,
        response_format: Type[T],
        use_search: bool = False,
    ) -> T:
        schema_hint = (
            "\n\nOutput must be a single JSON object (no markdown fences) "
            "matching exactly this JSON Schema:\n"
            + json.dumps(response_format.model_json_schema(), ensure_ascii=False)
        )

        kwargs: dict = {
            "model": self.model,
            "instructions": system + schema_hint,
            "input": user,
            "text": {"format": {"type": "json_object"}},
        }
        if use_search:
            kwargs["tools"] = [{"type": "web_search"}]

        completion = self.client.responses.create(**kwargs)

        if completion.usage is None:
            raise RuntimeError("LLM response missing usage information")

        self.cost_tracker.add_llm_call(completion.usage.input_tokens, completion.usage.output_tokens)

        if not completion.output_text:
            raise RuntimeError("LLM did not produce valid structured output")

        try:
            data = json.loads(_extract_json(completion.output_text))
            return response_format.model_validate(data)
        except (json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError(f"LLM did not produce valid structured output: {exc}") from exc
