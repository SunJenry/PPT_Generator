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
    """Robustly extract a JSON payload from LLM output.

    Handles these cases (in order):
    1. Pure JSON starting with {
    2. Markdown-fenced JSON (```json ... ```)
    3. JSON object embedded in natural language text (brace-counting)
    """
    text = content.strip()

    # Case 1-2: markdown-fenced or pure JSON
    if text.startswith("```"):
        text = _FENCE_RE.sub("", text).strip()
    if text.startswith("{"):
        return text

    # Case 3: JSON somewhere in the middle of natural language text.
    # Find the first '{' and count braces to find the matching '}'.
    start = text.find("{")
    if start == -1:
        return text  # no JSON at all

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue
        if ch == '"':
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return text[start : i + 1]

    return text  # unbalanced — return original


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
        }
        if use_search:
            kwargs["tools"] = [{"type": "web_search"}]
            # web_search uses internal reasoning rounds which consume output
            # tokens. Reserve ample budget so the JSON doesn't get truncated.
            kwargs["max_output_tokens"] = 32768
            # NOTE: json_object format conflicts with web_search on DeepSeek.
            # We rely on prompt instructions for JSON output instead.
        else:
            kwargs["text"] = {"format": {"type": "json_object"}}

        completion = self.client.responses.create(**kwargs)

        if completion.usage is None:
            raise RuntimeError("LLM response missing usage information")

        self.cost_tracker.add_llm_call(completion.usage.input_tokens, completion.usage.output_tokens)

        if not completion.output_text:
            raise RuntimeError("LLM did not produce valid structured output")

        raw_text = completion.output_text
        extracted = _extract_json(raw_text)

        # Debug: save failed output for diagnosis
        if not extracted.startswith("{"):
            try:
                with open("/tmp/llm_debug_fail.txt", "w", encoding="utf-8") as f:
                    f.write(f"=== Raw output ({len(raw_text)} chars) ===\n")
                    f.write(raw_text[:3000])
                    f.write("\n\n=== Extracted ===\n")
                    f.write(extracted[:2000])
            except OSError:
                pass

        try:
            data = json.loads(extracted)
            return response_format.model_validate(data)
        except (json.JSONDecodeError, ValueError) as exc:
            # Save full raw text on parse failure for inspection
            try:
                with open("/tmp/llm_debug_fail.txt", "w", encoding="utf-8") as f:
                    f.write(f"Parse error: {exc}\n\n")
                    f.write(f"=== Raw output ({len(raw_text)} chars) ===\n")
                    f.write(raw_text[:5000])
                    f.write("\n\n=== Extracted ===\n")
                    f.write(extracted[:3000])
            except OSError:
                pass
            raise RuntimeError(
                f"LLM did not produce valid structured output: {exc}. "
                f"Raw output saved to /tmp/llm_debug_fail.txt"
            ) from exc
