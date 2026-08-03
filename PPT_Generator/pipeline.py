import sys
import time

from PPT_Generator.config import settings
from PPT_Generator.content_generator import ContentGenerator
from PPT_Generator.cost_tracker import CostTracker
from PPT_Generator.image_search import ImageSearchClient
from PPT_Generator.llm_client import LLMClient
from PPT_Generator.planner import Planner
from PPT_Generator.renderer import Renderer
from PPT_Generator.templates.registry import TemplateRegistry
from PPT_Generator.validator import Validator


class Pipeline:
    def __init__(self):
        self.cost_tracker = CostTracker()
        self.llm_client = LLMClient(self.cost_tracker)
        self.image_client = ImageSearchClient(self.cost_tracker)
        self.templates = TemplateRegistry()

        self.planner = Planner(self.llm_client)
        self.content_generator = ContentGenerator(self.llm_client)
        self.validator = Validator(self.llm_client)
        self.renderer = Renderer(self.templates, self.image_client)

    def run(self, topic: str, brief: str, audience: str, output_path: str) -> dict:
        t_start = time.time()
        print(f"PPT Generator starting...")
        print(f"  Topic: {topic}")
        print(f"  Audience: {audience}")
        print(f"  Model: {settings.deepseek_model}")
        print()

        # ── Stage 1: Planner ──────────────────────────────────────────
        print("[1/4] Planner — generating narrative outline...")
        t0 = time.time()
        try:
            outline = self.planner.plan(topic, brief, audience)
        except Exception:
            print("Pipeline error: Planner stage failed.", file=sys.stderr)
            raise
        elapsed = time.time() - t0
        section_count = len(outline.sections)
        total_planned = sum(s.pages for s in outline.sections)
        print(f"       ✓ {section_count} sections, {total_planned} planned slides ({elapsed:.1f}s)")
        print()

        # ── Stage 2: Content Generator ─────────────────────────────────
        print("[2/4] Content Generator — generating slide content with web_search...")
        print("       (this stage may take 1-5 minutes)")
        t0 = time.time()
        try:
            presentation = self.content_generator.generate(topic, audience, outline, self.templates)
        except Exception:
            print("Pipeline error: ContentGenerator stage failed.", file=sys.stderr)
            raise
        elapsed = time.time() - t0
        source_count = len(presentation.sources)
        print(f"       ✓ {presentation.total_pages} slides, {source_count} sources ({elapsed:.1f}s)")
        print()

        # ── Stage 3: Validator ─────────────────────────────────────────
        print("[3/4] Validator — checking page count and coherence...")
        t0 = time.time()
        try:
            presentation = self.validator.validate(presentation, self.templates)
        except Exception:
            print("Pipeline error: Validator stage failed, using un-validated presentation.", file=sys.stderr)
        elapsed = time.time() - t0
        print(f"       ✓ {presentation.total_pages} slides validated ({elapsed:.1f}s)")
        print()

        # ── Stage 4: Renderer ──────────────────────────────────────────
        print(f"[4/4] Renderer — rendering {presentation.total_pages} slides to PPTX...")
        t0 = time.time()
        try:
            self.renderer.render(presentation, output_path)
        except Exception:
            print("Pipeline error: Renderer stage failed.", file=sys.stderr)
            raise
        elapsed = time.time() - t0
        print(f"       ✓ rendering complete ({elapsed:.1f}s)")
        print()

        # ── Summary ────────────────────────────────────────────────────
        total_elapsed = time.time() - t_start
        report = self.cost_tracker.report()
        report["output_path"] = output_path
        report["total_pages"] = presentation.total_pages
        report["elapsed_seconds"] = total_elapsed
        return report
