"""GroupShape and related objects."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pptx.dml.effect import ShadowFormat
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.shapes.base import BaseShape
from pptx.util import lazyproperty

if TYPE_CHECKING:
    from pptx.action import ActionSetting
    from pptx.oxml.shapes.groupshape import CT_GroupShape
    from pptx.shapes.shapetree import GroupShapes
    from pptx.types import ProvidesPart


class GroupShape(BaseShape):
    """A shape that acts as a container for other shapes."""

    def __init__(self, grpSp: CT_GroupShape, parent: ProvidesPart):
        super().__init__(grpSp, parent)
        self._grpSp = grpSp

    @lazyproperty
    def click_action(self) -> ActionSetting:
        """Unconditionally raises `TypeError`.

        A group shape cannot have a click action or hover action.
        """
        raise TypeError("a group shape cannot have a click action")

    @property
    def has_text_frame(self) -> bool:
        """Unconditionally |False|.

        A group shape does not have a textframe and cannot itself contain text. This does not
        impact the ability of shapes contained by the group to each have their own text.
        """
        return False

    @lazyproperty
    def shadow(self) -> ShadowFormat:
        """|ShadowFormat| object representing shadow effect for this group.

        A |ShadowFormat| object is always returned, even when no shadow is explicitly defined on
        this group shape (i.e. when the group inherits its shadow behavior).
        """
        return ShadowFormat(self._grpSp.grpSpPr)

    @property
    def shape_type(self) -> MSO_SHAPE_TYPE:
        """Member of :ref:`MsoShapeType` identifying the type of this shape.

        Unconditionally `MSO_SHAPE_TYPE.GROUP` in this case
        """
        return MSO_SHAPE_TYPE.GROUP

    @lazyproperty
    def shapes(self) -> GroupShapes:
        """|GroupShapes| object for this group.

        The |GroupShapes| object provides access to the group's member shapes and provides methods
        for adding new ones.
        """
        from pptx.shapes.shapetree import GroupShapes

        return GroupShapes(self._element, self)

    # -- Tree functionality for FEP-020 --

    def get_tree(self, max_depth=2):
        """Generate a hierarchical tree view of this group shape and its contents.

        This method provides the "Wide-Angle" discovery view for FEP-020,
        allowing AI agents to quickly understand the structure and contents
        of a group shape without loading full object details.

        Args:
            max_depth (int): Maximum depth for recursive tree generation.
                Default 2. Controls how deep the tree traversal goes:
                - 0: Just this group node (no children)
                - 1: Group + immediate member shapes (no nested group children)  
                - 2: Group + member shapes + nested group children

        Returns:
            dict: Tree representation with structure:
                {
                    "_object_type": "GroupShape",
                    "_identity": {"shape_id": 5, "name": "Group 1", ...},
                    "access_path": "slides[0].shapes[2]",
                    "geometry": {"left": "2.0 in", "top": "1.0 in", ...},
                    "content_summary": "Group: 'Chart Group' (3 shapes)",
                    "children": [...] | None
                }

        Example:
            >>> group = slide.shapes[2]  # Assuming it's a group
            >>> tree = group.get_tree(max_depth=1)
            >>> print(tree['content_summary'])
            "Group: 'Chart Group' (3 shapes)"
        """
        # For group shapes called independently, we don't know the access path
        # This would typically be called from a parent container that provides the path
        access_path = f"group_shape_{self.shape_id}"
        return self._to_tree_node(access_path, max_depth, _current_depth=0)

    def _to_tree_node_content_summary(self):
        """Override to provide group-specific content summary for tree node representation."""
        summary_parts = []

        # Group identifier
        summary_parts.append("Group")

        # Add name if it's meaningful (not default pattern)
        if self.name and not self.name.startswith(("Group", "Grouped")):
            summary_parts.append(f"'{self.name}'")

        # Member shape count
        try:
            shape_count = len(self.shapes)
            if shape_count > 0:
                summary_parts.append(f"({shape_count} shape{'s' if shape_count != 1 else ''})")
            else:
                summary_parts.append("(empty)")
        except Exception:
            summary_parts.append("(unknown contents)")

        return " ".join(summary_parts)

    def _to_tree_node_children(self, access_path, max_depth, current_depth):
        """Override to provide group's member shapes as children."""
        if current_depth >= max_depth:
            return None

        children = []

        try:
            # Add member shapes
            for i, shape in enumerate(self.shapes):
                shape_access_path = f"{access_path}.shapes[{i}]"
                if hasattr(shape, '_to_tree_node'):
                    child_node = shape._to_tree_node(shape_access_path, max_depth, current_depth + 1)
                    children.append(child_node)
                else:
                    # Fallback for shapes without tree node support
                    children.append({
                        "_object_type": type(shape).__name__,
                        "_identity": {
                            "shape_id": getattr(shape, 'shape_id', 'unknown'),
                            "class_name": type(shape).__name__
                        },
                        "access_path": shape_access_path,
                        "geometry": None,
                        "content_summary": f"{type(shape).__name__} object",
                        "children": None
                    })

        except Exception:
            # If we can't access shapes, return empty children list
            pass

        return children if children else None
