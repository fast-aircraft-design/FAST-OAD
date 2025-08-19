"""
Sphinx directives for listing the paramaters of a segment, and the segments that use a
parameter.
"""

from abc import ABC, abstractmethod
from dataclasses import fields
from typing import List, Tuple

from docutils import nodes
from sphinx.util.docutils import SphinxDirective

from fastoad.models.performances.mission.segments.base import RegisterSegment


class AbstractLinkList(SphinxDirective, ABC):
    """
    Abstract class for producing an admonition that contains a list of keywords and
    these keywords will be hyperlinks if the associated target exists.

    Method .get_text_and_targets() must be implemented to provide the list
    of tuples (keyword, target).
    """

    has_content = True

    header_text = None

    @abstractmethod
    def get_text_and_targets(self) -> List[Tuple[str, str]]:
        """
        :return: a list of tuples for future hyperlinks (displayed text, rst target)
        """

    def run(self):
        # Rationale: we want the admonition content to be an enumeration of "keywords" that will
        # link to their definition... if the target existes in the rst file.
        # But at this point in the process, the check can be done only on rst content parsed
        # before the point of the directive.
        # Then we need to put a placeholder (an empty paragraph node) that will be filled later,
        # once all rst content has been processed.
        # For this, we populate the custom field env.target_data with the needed information,
        # the result of self.get_text_and_targets(), associated with the created placeholder.

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

        # HTML class name for CSS styling
        admonition_node["classes"].append("admonition")
        admonition_node["classes"].append(self.header_text.lower().replace(" ", "-"))

        # Registering data for later processing
        env.app.env.target_data.append((self.get_text_and_targets(), place_holder))

        return [admonition_node]


class ListSegmentsForAttribute(AbstractLinkList):
    """
    This Sphinx directive creates an "Apply to" admonition that lists segments that contain
    the provided attribute.

    The listed segment keywords will be references to paragraphs (i.e., hyperlinks in the generated
    doc), if the matching paragraphs are tagged like `segment-<segment keyword>` (with all "_" in
    the segment keyword replaced by "-")

    e.g. for "ground_speed_change":
        .. _segment-ground-speed-change:
    """

    header_text = "Applies to"

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

    The listed attributes will be references to paragraphs (i.e., hyperlinks in the generated
    doc), if the matching paragraphs are tagged like `segment-parameter-<attribute name>` (with
    all "_" in the attribute name replaced by "-")

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


def check_targets(app, doctree):
    """
    Executed after all rst files have been parsed.

    Populates all created placeholders with list of proper text/hyperlinks.
    """

    # Retrieving the env.target_data populated in the directives.
    if not hasattr(app.env, "target_data"):
        return
    target_data = app.env.target_data

    for target_list, directive_location in target_data:
        if len(directive_location.children) > 0:
            # If directive_location already has children, it has already been processed,
            # there is nothing to do.
            continue

        child_nodes = _generate_hyperlink_list(app, doctree, target_list)

        directive_location += child_nodes


def _generate_hyperlink_list(app, doctree, target_list):
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
    child_nodes.pop()  # Removing the trailing "/" (was the easiest way I found)
    return child_nodes


def setup(app):
    """
    Sphinx registering.
    """
    app.add_directive("list-segments-for", ListSegmentsForAttribute)
    app.add_directive("list-attributes-for", ListSegmentAttributes)

    # Here we connect the method that will run after first parsing
    app.connect("doctree-read", check_targets)
