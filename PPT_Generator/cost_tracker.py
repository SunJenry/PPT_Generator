import time
from dataclasses import dataclass, field
from typing import Dict


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
        # Approximate RMB costs (kimi-k2.6 prompt ~0.0015/1k, completion ~0.006/1k; Tavily basic ~0.025/search)
        llm_cost = (self.llm_prompt_tokens * 0.0015 + self.llm_completion_tokens * 0.006) / 1000
        search_cost = self.search_calls * 0.025
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
