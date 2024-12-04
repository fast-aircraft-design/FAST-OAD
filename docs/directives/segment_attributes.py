from abc import ABC, abstractmethod
from dataclasses import fields
from typing import List, Tuple

from docutils import nodes
from fastoad.models.performances.mission.segments.base import RegisterSegment
from sphinx.util.docutils import SphinxDirective


def target_exists(document, target_name):
    # Check if the target already exists in the document
    for node in document.findall(nodes.target):
        if target_name in node["ids"]:
            return True

    return False


class AbstractLinkList(SphinxDirective, ABC):
    has_content = True

    header_text = None

    @abstractmethod
    def get_text_and_targets(self) -> List[Tuple[str, str]]:
        pass

    def run(self):
        child_nodes = []
        for text, target_id in self.get_text_and_targets():
            if target_exists(self.state.document, target_id):
                reference_node = nodes.reference(
                    refuri=f"#{target_id}",
                    text=text,
                    internal=True,
                )
                child_nodes.append(reference_node)
            else:
                msg = f'list-segments-for: Target "{target_id}" not found.'
                self.state.document.reporter.warning(msg)
                child_nodes.append(nodes.Text(text))

        return self.get_list_admonition(child_nodes)

    def _get_list_admonition(self, content_nodes):
        child_nodes = []
        for node in content_nodes:
            child_nodes.append(node)
            child_nodes.append(nodes.Text(" / "))
        child_nodes.pop()  # Removing the last "/"

        node = nodes.admonition(
            "",
            nodes.title(
                "",
                self.header_text,
            ),
            nodes.paragraph(
                "",
                "",
                *child_nodes,
            ),
        )

        return [node]


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
