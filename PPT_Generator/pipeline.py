import sys

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
        try:
            outline = self.planner.plan(topic, brief, audience)
        except Exception:
            print("Pipeline error: Planner stage failed.", file=sys.stderr)
            raise

        try:
            presentation = self.content_generator.generate(topic, audience, outline, self.templates)
        except Exception:
            print("Pipeline error: ContentGenerator stage failed.", file=sys.stderr)
            raise

        try:
            presentation = self.validator.validate(presentation, self.templates)
        except Exception:
            print("Pipeline error: Validator stage failed, using un-validated presentation.", file=sys.stderr)

        try:
            self.renderer.render(presentation, output_path)
        except Exception:
            print("Pipeline error: Renderer stage failed.", file=sys.stderr)
            raise

        report = self.cost_tracker.report()
        report["output_path"] = output_path
        report["total_pages"] = presentation.total_pages
        return report
