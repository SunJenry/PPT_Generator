from PPT_Generator.cost_tracker import CostTracker


def test_cost_tracker_accumulates():
    ct = CostTracker()
    ct.add_llm_call(1000, 500)
    ct.add_search_call()
    ct.add_image_call()
    report = ct.report()
    assert report["llm_prompt_tokens"] == 1000
    assert report["llm_completion_tokens"] == 500
    assert report["llm_call_count"] == 1
    assert report["search_calls"] == 1
    assert report["image_calls"] == 1
    assert report["estimated_cost_rmb"] > 0
