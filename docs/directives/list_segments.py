from docutils import nodes
from fastoad.models.performances.mission.segments.base import RegisterSegment
from sphinx.util.docutils import SphinxDirective


class ListSegmentsForAttribute(SphinxDirective):
    """
    This Sphinx directive creates an "Apply to" admonition that lists segments that contain
    the provided attribute.

    The list will be references to paragraphs, provided they are tagged like
    `segment-<segment keyword>` (with all "_" replaced by "-")

    e.g. for "ground_speed_change":
        .. _segment-ground-speed-change:
    """

    has_content = True

    def run(self):
        attribute_name = self.content[0].strip()

        class_dict = RegisterSegment.get_classes()
        segment_keywords = sorted(list(class_dict))

        valid_keywords = [
            keyword for keyword in segment_keywords if hasattr(class_dict[keyword], attribute_name)
        ]

        child_nodes = []
        for keyword in valid_keywords:
            target_id = f"segment-{keyword}".replace("_", "-")
            if self.target_exists(target_id):
                reference_node = nodes.reference(
                    refuri=f"#{target_id}",
                    text=keyword,
                    internal=True,
                )
                child_nodes.append(reference_node)
            else:
                msg = f'list-segments-for: Target "{target_id}" not found.'
                self.state.document.reporter.warning(msg)
                child_nodes.append(nodes.Text(keyword))

            child_nodes.append(nodes.Text(" / "))

        child_nodes.pop()  # Removing the last "/"

        node = nodes.admonition(
            "",
            nodes.title("", "Applies to"),
            nodes.paragraph(
                "",
                "",
                *child_nodes,
            ),
        )

        return [node]

    def target_exists(self, target_name):
        # Check if the target already exists in the document
        for node in self.state.document.traverse(nodes.target):
            if target_name in node["ids"]:
                return True

        return False


def setup(app):
    app.add_directive("list-segments-for", ListSegmentsForAttribute)
