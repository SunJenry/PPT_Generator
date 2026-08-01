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
    report = pipeline.run(topic, brief, audience, args.output)
    print(f"Generated {report['total_pages']} slides to {report['output_path']}")
    print(f"Estimated cost: ¥{report['estimated_cost_rmb']}, elapsed: {report['elapsed_seconds']:.1f}s")


if __name__ == "__main__":
    main()
