from abc import ABC, abstractmethod
from dataclasses import fields
from typing import List, Tuple

from docutils import nodes
from fastoad.models.performances.mission.segments.base import RegisterSegment
from sphinx.util.docutils import SphinxDirective


def check_targets(app, doctree):
    if not hasattr(app.env, "target_data"):
        return
    target_data = app.env.target_data

    if target_data:
        for target_list, directive_location in target_data:
            if len(directive_location.children) > 0:
                continue
            child_nodes = []
            for text, target_name in target_list:
                target_exists = target_name in app.env.domaindata["std"]["labels"]
                if target_exists:
                    reference_node = nodes.reference(
                        refuri=f"#{target_name}",
                        text=text,
                        internal=True,
                    )
                    child_nodes.append(reference_node)
                else:
                    msg = f'Target "{target_name}" not found. Using simple text.'
                    doctree.reporter.warning(msg)
                    child_nodes.append(nodes.Text(text))
                child_nodes.append(nodes.Text(" / "))
            child_nodes.pop()
            directive_location += child_nodes


class AbstractLinkList(SphinxDirective, ABC):
    has_content = True

    header_text = None

    @abstractmethod
    def get_text_and_targets(self) -> List[Tuple[str, str]]:
        pass

    def run(self):
        # Store the target names and their locations in the environment
        env = self.state.document.settings.env
        if not hasattr(env, "target_data"):
            env.target_data = []  # Initialize if not present

        # Create a placeholder paragraph node
        place_holder = nodes.paragraph()

        admonition_node = nodes.admonition(
            "",
            nodes.title("", self.header_text),
            place_holder,
        )
        env.app.env.target_data.append((self.get_text_and_targets(), place_holder))

        return [admonition_node]


class ListSegmentsForAttribute(AbstractLinkList):
    """
    This Sphinx directive creates an "Apply to" admonition that lists segments that contain
    the provided attribute.

    The list will be references to paragraphs, provided they are tagged like
    `segment-<segment keyword>` (with all "_" replaced by "-")

    e.g. for "ground_speed_change":
        .. _segment-ground-speed-change:
    """

    header_text = "Applies_to"

    def get_text_and_targets(self):
        attribute_name = self.content[0].strip()

        class_dict = RegisterSegment.get_classes()
        segment_keywords = sorted(list(class_dict))

        valid_keywords = [
            keyword for keyword in segment_keywords if hasattr(class_dict[keyword], attribute_name)
        ]

        return [(keyword, f"segment-{keyword}".replace("_", "-")) for keyword in valid_keywords]


class ListSegmentAttributes(AbstractLinkList):
    """
    This Sphinx directive creates a "Parameters" admonition that lists segment attributes.

    The list will be references to paragraphs, provided they are tagged like
    `segment-parameter-<attribute name>` (with all "_" replaced by "-")

    e.g. for "ground_speed_change":
        .. _segment-parameter-ground-speed-change:
    """

    header_text = "Parameters"

    def get_text_and_targets(self):
        segment_name = self.content[0].strip()

        segment_class = RegisterSegment.get_class(segment_name)

        segment_attributes = sorted(
            [f.name for f in fields(segment_class) if not f.name.startswith("_")]
        )

        return [
            (attr_name, f"segment-parameter-{attr_name}".replace("_", "-"))
            for attr_name in segment_attributes
        ]


def setup(app):
    app.add_directive("list-segments-for", ListSegmentsForAttribute)
    app.add_directive("list-attributes-for", ListSegmentAttributes)
    app.connect("doctree-read", check_targets)
