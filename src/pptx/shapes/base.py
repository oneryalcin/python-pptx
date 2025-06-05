"""Base shape-related objects such as BaseShape."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from pptx.action import ActionSetting
from pptx.dml.effect import ShadowFormat
from pptx.introspection import IntrospectionMixin
from pptx.oxml.simpletypes import XsdBoolean
from pptx.shared import ElementProxy
from pptx.util import lazyproperty

if TYPE_CHECKING:
    from pptx.enum.shapes import MSO_SHAPE_TYPE, PP_PLACEHOLDER
    from pptx.oxml.shapes import ShapeElement
    from pptx.oxml.shapes.shared import CT_Placeholder
    from pptx.parts.slide import BaseSlidePart
    from pptx.types import ProvidesPart
    from pptx.util import Length


class BaseShape(IntrospectionMixin):
    """Base class for shape objects.

    Subclasses include |Shape|, |Picture|, and |GraphicFrame|.
    """

    def __init__(self, shape_elm: ShapeElement, parent: ProvidesPart):
        super().__init__()
        self._element = shape_elm
        self._parent = parent

    def __eq__(self, other: object) -> bool:
        """|True| if this shape object proxies the same element as *other*.

        Equality for proxy objects is defined as referring to the same XML element, whether or not
        they are the same proxy object instance.
        """
        if not isinstance(other, BaseShape):
            return False
        return self._element is other._element

    def __ne__(self, other: object) -> bool:
        if not isinstance(other, BaseShape):
            return True
        return self._element is not other._element

    @lazyproperty
    def click_action(self) -> ActionSetting:
        """|ActionSetting| instance providing access to click behaviors.

        Click behaviors are hyperlink-like behaviors including jumping to a hyperlink (web page)
        or to another slide in the presentation. The click action is that defined on the overall
        shape, not a run of text within the shape. An |ActionSetting| object is always returned,
        even when no click behavior is defined on the shape.
        """
        cNvPr = self._element._nvXxPr.cNvPr  # pyright: ignore[reportPrivateUsage]
        return ActionSetting(cNvPr, self)

    @property
    def element(self) -> ShapeElement:
        """`lxml` element for this shape, e.g. a CT_Shape instance.

        Note that manipulating this element improperly can produce an invalid presentation file.
        Make sure you know what you're doing if you use this to change the underlying XML.
        """
        return self._element

    @property
    def has_chart(self) -> bool:
        """|True| if this shape is a graphic frame containing a chart object.

        |False| otherwise. When |True|, the chart object can be accessed using the ``.chart``
        property.
        """
        # This implementation is unconditionally False, the True version is
        # on GraphicFrame subclass.
        return False

    @property
    def has_table(self) -> bool:
        """|True| if this shape is a graphic frame containing a table object.

        |False| otherwise. When |True|, the table object can be accessed using the ``.table``
        property.
        """
        # This implementation is unconditionally False, the True version is
        # on GraphicFrame subclass.
        return False

    @property
    def has_text_frame(self) -> bool:
        """|True| if this shape can contain text."""
        # overridden on Shape to return True. Only <p:sp> has text frame
        return False

    @property
    def height(self) -> Length:
        """Read/write. Integer distance between top and bottom extents of shape in EMUs."""
        return self._element.cy

    @height.setter
    def height(self, value: Length):
        self._element.cy = value

    @property
    def is_placeholder(self) -> bool:
        """True if this shape is a placeholder.

        A shape is a placeholder if it has a <p:ph> element.
        """
        return self._element.has_ph_elm

    @property
    def left(self) -> Length:
        """Integer distance of the left edge of this shape from the left edge of the slide.

        Read/write. Expressed in English Metric Units (EMU)
        """
        return self._element.x

    @left.setter
    def left(self, value: Length):
        self._element.x = value

    @property
    def name(self) -> str:
        """Name of this shape, e.g. 'Picture 7'."""
        return self._element.shape_name

    @name.setter
    def name(self, value: str):
        self._element._nvXxPr.cNvPr.name = value  # pyright: ignore[reportPrivateUsage]

    @property
    def part(self) -> BaseSlidePart:
        """The package part containing this shape.

        A |BaseSlidePart| subclass in this case. Access to a slide part should only be required if
        you are extending the behavior of |pp| API objects.
        """
        return cast("BaseSlidePart", self._parent.part)

    @property
    def placeholder_format(self) -> _PlaceholderFormat:
        """Provides access to placeholder-specific properties such as placeholder type.

        Raises |ValueError| on access if the shape is not a placeholder.
        """
        ph = self._element.ph
        if ph is None:
            raise ValueError("shape is not a placeholder")
        return _PlaceholderFormat(ph)

    @property
    def rotation(self) -> float:
        """Degrees of clockwise rotation.

        Read/write float. Negative values can be assigned to indicate counter-clockwise rotation,
        e.g. assigning -45.0 will change setting to 315.0.
        """
        return self._element.rot

    @rotation.setter
    def rotation(self, value: float):
        self._element.rot = value

    @lazyproperty
    def shadow(self) -> ShadowFormat:
        """|ShadowFormat| object providing access to shadow for this shape.

        A |ShadowFormat| object is always returned, even when no shadow is
        explicitly defined on this shape (i.e. it inherits its shadow
        behavior).
        """
        return ShadowFormat(self._element.spPr)

    @property
    def shape_id(self) -> int:
        """Read-only positive integer identifying this shape.

        The id of a shape is unique among all shapes on a slide.
        """
        return self._element.shape_id

    @property
    def shape_type(self) -> MSO_SHAPE_TYPE:
        """A member of MSO_SHAPE_TYPE classifying this shape by type.

        Like ``MSO_SHAPE_TYPE.CHART``. Must be implemented by subclasses.
        """
        raise NotImplementedError(f"{type(self).__name__} does not implement `.shape_type`")

    @property
    def top(self) -> Length:
        """Distance from the top edge of the slide to the top edge of this shape.

        Read/write. Expressed in English Metric Units (EMU)
        """
        return self._element.y

    @top.setter
    def top(self, value: Length):
        self._element.y = value

    @property
    def width(self) -> Length:
        """Distance between left and right extents of this shape.

        Read/write. Expressed in English Metric Units (EMU).
        """
        return self._element.cx

    @width.setter
    def width(self, value: Length):
        self._element.cx = value

    @property
    def visible(self):
        """
        Read/write. Returns or sets the visibility of the specified object or the formatting applied
        to the specified object.
        """
        return not self._element.hidden

    @visible.setter
    def visible(self, value):
        self._element._nvXxPr.cNvPr.set("hidden", XsdBoolean.convert_to_xml(not value))

    # -- IntrospectionMixin overrides --

    def _to_dict_identity(
        self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private
    ):
        """Override to include shape-specific identity information."""
        identity = super()._to_dict_identity(
            _visited_ids, max_depth, expand_collections, format_for_llm, include_private
        )

        # Basic shape identification
        identity["shape_id"] = self.shape_id
        identity["name"] = self.name
        identity["is_placeholder"] = self.is_placeholder

        # Shape type (with safe error handling)
        shape_type = self._get_shape_type_safely()
        if shape_type is not None:
            identity["shape_type"] = self._format_property_value_for_to_dict(
                shape_type,
                include_private,
                _visited_ids,
                max_depth,
                expand_collections,
                format_for_llm,
            )

        # Placeholder details (if applicable)
        placeholder_info = self._get_placeholder_info_safely(
            include_private, _visited_ids, max_depth, expand_collections, format_for_llm
        )
        if placeholder_info is not None:
            identity["placeholder_details"] = placeholder_info

        return identity

    def _to_dict_properties(
        self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
    ):
        """Override to include shape geometry properties."""
        # Get base properties (empty dict from IntrospectionMixin)
        props = super()._to_dict_properties(
            include_private, _visited_ids, max_depth, expand_collections, format_for_llm
        )

        # Add geometry properties
        geometry_props = {
            "left": self.left,
            "top": self.top,
            "width": self.width,
            "height": self.height,
            "rotation": self.rotation,
        }

        for name, value in geometry_props.items():
            props[name] = self._format_property_value_for_to_dict(
                value,
                include_private,
                _visited_ids,
                max_depth - 1,
                expand_collections,
                format_for_llm,
            )

        return props

    def _to_dict_relationships(
        self, remaining_depth, expand_collections, _visited_ids, format_for_llm, include_private
    ):
        """Override to include parent collection and part relationships."""
        rels = super()._to_dict_relationships(
            remaining_depth, expand_collections, _visited_ids, format_for_llm, include_private
        )

        # Parent collection (shapes collection)
        if self._parent is not None:
            if hasattr(self._parent, "to_dict") and callable(getattr(self._parent, "to_dict")):
                try:
                    rels["parent_collection"] = self._parent.to_dict(
                        include_relationships=False,
                        max_depth=0,  # Just a summary
                        include_private=include_private,
                        expand_collections=False,
                        format_for_llm=format_for_llm,
                        _visited_ids=_visited_ids,
                    )
                except Exception:
                    # Fallback to repr if to_dict fails
                    rels["parent_collection"] = repr(self._parent)
            else:
                # Fallback to repr if no to_dict method
                rels["parent_collection"] = repr(self._parent)

        # Part information
        try:
            part = self.part
            if hasattr(part, "to_dict") and callable(getattr(part, "to_dict")):
                try:
                    rels["part"] = part.to_dict(
                        include_relationships=False,
                        max_depth=0,  # Just a summary
                        include_private=include_private,
                        expand_collections=False,
                        format_for_llm=format_for_llm,
                        _visited_ids=_visited_ids,
                    )
                except Exception:
                    # Fallback to repr if to_dict fails
                    rels["part"] = repr(part)
            else:
                # Fallback to repr if no to_dict method
                rels["part"] = repr(part)
        except Exception:
            # Handle case where part access might fail
            rels["part"] = None

        return rels

    def _to_dict_llm_context(
        self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private
    ):
        """Override to provide shape-specific LLM context."""
        context = super()._to_dict_llm_context(
            _visited_ids, max_depth, expand_collections, format_for_llm, include_private
        )

        # Build descriptive context
        desc_parts = []

        # Shape type description
        shape_type = self._get_shape_type_safely()
        if shape_type is not None:
            desc_parts.append(f"A {shape_type.name} shape")
        else:
            desc_parts.append("A shape")

        # Name and ID
        desc_parts.append(f"named '{self.name}' (ID: {self.shape_id})")

        # Placeholder context
        if self.is_placeholder:
            placeholder_info = self._get_placeholder_info_safely(
                include_private, _visited_ids, max_depth, expand_collections, format_for_llm
            )
            if placeholder_info and isinstance(placeholder_info, dict):
                # Try the new structure (from _PlaceholderFormat.to_dict())
                if "properties" in placeholder_info and "type" in placeholder_info["properties"]:
                    ph_type = placeholder_info["properties"]["type"]
                    if isinstance(ph_type, dict) and "name" in ph_type:
                        desc_parts.append(f"serving as a {ph_type['name']} placeholder")
                    else:
                        desc_parts.append("serving as a placeholder")
                # Try the old structure (fallback for backwards compatibility)
                elif "type" in placeholder_info:
                    ph_type = placeholder_info["type"]
                    if isinstance(ph_type, dict) and "name" in ph_type:
                        desc_parts.append(f"serving as a {ph_type['name']} placeholder")
                    else:
                        desc_parts.append("serving as a placeholder")
                else:
                    desc_parts.append("serving as a placeholder")

        context["description"] = " ".join(desc_parts) + "."

        # Common operations
        context["common_operations"] = [
            "access geometry (left, top, width, height, rotation)",
            "modify position and size",
            "change name",
            "access shape type information",
        ]

        if self.is_placeholder:
            context["common_operations"].append("access placeholder format details")

        return context

    # -- Tree node overrides for FEP-020 --

    def _to_tree_node_identity(self):
        """Override to provide rich shape identity for tree node representation."""
        identity = {
            "shape_id": self.shape_id,
            "name": self.name,
            "class_name": type(self).__name__,
        }

        # Add shape type if available
        shape_type = self._get_shape_type_safely()
        if shape_type is not None:
            identity["shape_type"] = shape_type.name

        # Add placeholder information if applicable
        if self.is_placeholder:
            try:
                placeholder_format = self.placeholder_format
                identity["placeholder_type"] = placeholder_format.type.name
                identity["placeholder_idx"] = placeholder_format.idx
            except (ValueError, AttributeError):
                identity["placeholder_type"] = "UNKNOWN"

        return identity

    def _to_tree_node_geometry(self):
        """Override to provide shape geometry for tree node representation."""
        try:
            return {
                "left": f"{self.left.inches:.2f} in",
                "top": f"{self.top.inches:.2f} in",
                "width": f"{self.width.inches:.2f} in",
                "height": f"{self.height.inches:.2f} in",
                "rotation": f"{self.rotation:.1f}°" if self.rotation != 0 else "0°",
            }
        except Exception:
            # Fallback if geometry access fails
            return None

    def _to_tree_node_content_summary(self):
        """Override to provide shape content summary for tree node representation."""
        # Build summary parts
        summary_parts = []

        # Shape type and name
        shape_type = self._get_shape_type_safely()
        if shape_type:
            summary_parts.append(f"{shape_type.name}")
        else:
            summary_parts.append("Shape")

        # Add name if different from default pattern
        if self.name and not self.name.startswith((type(self).__name__, "Shape")):
            summary_parts.append(f"'{self.name}'")

        # Placeholder context
        if self.is_placeholder:
            try:
                placeholder_format = self.placeholder_format
                ph_type = placeholder_format.type.name
                summary_parts.append(f"({ph_type} placeholder)")
            except (ValueError, AttributeError):
                summary_parts.append("(placeholder)")

        # Text content hint for shapes with text frames
        if hasattr(self, 'has_text_frame') and self.has_text_frame:
            try:
                if hasattr(self, 'text_frame') and hasattr(self, 'text'):
                    text_content = self.text.strip()  # type: ignore
                    if text_content:
                        # Truncate long text
                        if len(text_content) > 30:
                            text_content = text_content[:27] + "..."
                        summary_parts.append(f"Text: '{text_content}'")
                    else:
                        summary_parts.append("(empty text)")
            except Exception:
                summary_parts.append("(text frame)")

        # Chart/table context
        if hasattr(self, 'has_chart') and self.has_chart:
            summary_parts.append("(contains chart)")
        elif hasattr(self, 'has_table') and self.has_table:
            summary_parts.append("(contains table)")

        return " ".join(summary_parts)

    # -- Helper methods for safe property access --

    def _get_shape_type_safely(self):
        """Get shape_type with safe error handling for BaseShape."""
        try:
            return self.shape_type
        except NotImplementedError:
            # BaseShape doesn't implement shape_type, subclasses do
            return None
        except Exception:
            # Handle any other unexpected errors
            return None

    def _get_placeholder_info_safely(
        self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
    ):
        """Get placeholder information with safe error handling."""
        if not self.is_placeholder:
            return None

        try:
            # Use PlaceholderFormat.to_dict() instead of manually constructing
            return self.placeholder_format.to_dict(
                max_depth=max_depth - 1,  # It's a component property
                _visited_ids=_visited_ids,
                include_relationships=False,  # PlaceholderFormat has no relationships
                expand_collections=False,  # PlaceholderFormat has no collections
                format_for_llm=format_for_llm,
                include_private=include_private,
            )
        except (ValueError, AttributeError) as e:
            # Return error context instead of failing
            return self._create_error_context(
                "placeholder_format", e, "Failed to get placeholder details"
            )


class _PlaceholderFormat(ElementProxy, IntrospectionMixin):
    """Provides properties specific to placeholders, such as the placeholder type.

    Accessed via the :attr:`~.BaseShape.placeholder_format` property of a placeholder shape,
    """

    def __init__(self, element: CT_Placeholder):
        super().__init__(element)
        IntrospectionMixin.__init__(self)
        self._ph = element

    @property
    def element(self) -> CT_Placeholder:
        """The `p:ph` element proxied by this object."""
        return self._ph

    @property
    def idx(self) -> int:
        """Integer placeholder 'idx' attribute."""
        return self._ph.idx

    @property
    def type(self) -> PP_PLACEHOLDER:
        """Placeholder type.

        A member of the :ref:`PpPlaceholderType` enumeration, e.g. PP_PLACEHOLDER.CHART
        """
        return self._ph.type

    # -- IntrospectionMixin overrides --

    def _to_dict_identity(
        self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private
    ):
        """Override to include placeholder-specific identity information."""
        identity = super()._to_dict_identity(
            _visited_ids, max_depth, expand_collections, format_for_llm, include_private
        )

        # Add placeholder-specific description
        type_name = self.type.name if self.type else "UNDEFINED_TYPE"
        identity["description"] = f"Details for a {type_name} placeholder (idx: {self.idx})."

        return identity

    def _to_dict_properties(
        self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
    ):
        """Override to include placeholder properties."""
        props = super()._to_dict_properties(
            include_private, _visited_ids, max_depth, expand_collections, format_for_llm
        )

        # Add core placeholder properties
        props["idx"] = self.idx  # Integer
        props["type"] = self._format_property_value_for_to_dict(
            self.type,
            include_private,
            _visited_ids,
            max_depth - 1,
            expand_collections,
            format_for_llm,
        )  # PP_PLACEHOLDER enum

        return props

    def _to_dict_relationships(
        self, remaining_depth, expand_collections, _visited_ids, format_for_llm, include_private
    ):
        """Override to include relationships (none for PlaceholderFormat)."""
        # PlaceholderFormat is a simple property bag with no relationships
        return super()._to_dict_relationships(
            remaining_depth, expand_collections, _visited_ids, format_for_llm, include_private
        )

    def _to_dict_llm_context(
        self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private
    ):
        """Override to provide placeholder-specific LLM context."""
        context = super()._to_dict_llm_context(
            _visited_ids, max_depth, expand_collections, format_for_llm, include_private
        )

        type_name = self.type.name if self.type else "UNDEFINED_TYPE"
        context["description"] = (
            f"Placeholder attributes: Type is {type_name}, Index is {self.idx}."
        )
        context["summary"] = context["description"]
        context["common_operations"] = [
            "identify placeholder role (e.g., TITLE, BODY, PICTURE)",
            "get unique index (idx) for matching with layout/master",
        ]

        return context
