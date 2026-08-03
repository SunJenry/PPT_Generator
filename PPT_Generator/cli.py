import argparse
import json
import sys

from PPT_Generator.pipeline import Pipeline


def main(argv=None):
    parser = argparse.ArgumentParser(description="Generate a PPT from JSON input.")
    parser.add_argument("input", help="Path to input JSON file")
    parser.add_argument("output", help="Path to output .pptx file")
    args = parser.parse_args(argv)

    with open(args.input, "r", encoding="utf-8") as f:
        data = json.load(f)

    topic = data.get("topic", "")
    brief = data.get("brief", "")
    audience = data.get("audience", "")

    if not topic or not brief or not audience:
        print("Error: input JSON must contain topic, brief, and audience.", file=sys.stderr)
        sys.exit(1)

    pipeline = Pipeline()
    try:
        report = pipeline.run(topic, brief, audience, args.output)
    except Exception as e:
        print(f"Error: PPT generation failed: {e}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print(f"  Output:      {report['output_path']}")
    print(f"  Slides:      {report['total_pages']} pages")
    print(f"  Cost:        ¥{report['estimated_cost_rmb']:.4f}")
    print(f"  Time:        {report['elapsed_seconds']:.1f}s ({report['elapsed_seconds']/report['total_pages']:.1f}s/slide)")
    print(f"  LLM calls:   {report['llm_call_count']}")
    print(f"  Tokens:      {report['llm_prompt_tokens']:,} in / {report['llm_completion_tokens']:,} out")
    print(f"  Images:      {report['image_calls']} fetched")
    print("=" * 60)


if __name__ == "__main__":
    main()
