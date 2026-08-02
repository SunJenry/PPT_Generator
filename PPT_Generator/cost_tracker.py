import time
from dataclasses import dataclass, field
from typing import Dict

# DeepSeek v4-flash pricing, RMB per 1k tokens (off-peak)
PROMPT_COST_PER_1K = 0.001  # ¥1 per 1M input tokens (cache miss)
COMPLETION_COST_PER_1K = 0.002  # ¥2 per 1M output tokens


@dataclass
class CostTracker:
    llm_prompt_tokens: int = 0
    llm_completion_tokens: int = 0
    search_calls: int = 0
    image_calls: int = 0
    start_time: float = field(default_factory=time.time)

    def add_llm_call(self, prompt_tokens: int, completion_tokens: int) -> None:
        self.llm_prompt_tokens += prompt_tokens
        self.llm_completion_tokens += completion_tokens

    def add_search_call(self) -> None:
        self.search_calls += 1

    def add_image_call(self) -> None:
        self.image_calls += 1

    def report(self) -> Dict:
        elapsed = time.time() - self.start_time
        llm_cost = (
            self.llm_prompt_tokens * PROMPT_COST_PER_1K
            + self.llm_completion_tokens * COMPLETION_COST_PER_1K
        ) / 1000
        search_cost = self.search_calls * 0.01
        image_cost = self.image_calls * 0.01
        total = llm_cost + search_cost + image_cost
        return {
            "elapsed_seconds": elapsed,
            "llm_prompt_tokens": self.llm_prompt_tokens,
            "llm_completion_tokens": self.llm_completion_tokens,
            "search_calls": self.search_calls,
            "image_calls": self.image_calls,
            "estimated_cost_rmb": round(total, 4),
        }
