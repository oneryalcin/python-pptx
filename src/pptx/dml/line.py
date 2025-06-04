"""DrawingML objects related to line formatting."""

from __future__ import annotations

from pptx.dml.fill import FillFormat
from pptx.enum.dml import MSO_FILL
from pptx.introspection import IntrospectionMixin
from pptx.util import Emu, lazyproperty


class LineFormat(IntrospectionMixin):
    """Provides access to line properties such as color, style, and width.

    A LineFormat object is typically accessed via the ``.line`` property of
    a shape such as |Shape| or |Picture|.
    """

    def __init__(self, parent):
        super(LineFormat, self).__init__()
        self._parent = parent

    @lazyproperty
    def color(self):
        """
        The |ColorFormat| instance that provides access to the color settings
        for this line. Essentially a shortcut for ``line.fill.fore_color``.
        As a side-effect, accessing this property causes the line fill type
        to be set to ``MSO_FILL.SOLID``. If this sounds risky for your use
        case, use ``line.fill.type`` to non-destructively discover the
        existing fill type.
        """
        if self.fill.type != MSO_FILL.SOLID:
            self.fill.solid()
        return self.fill.fore_color

    @property
    def dash_style(self):
        """Return value indicating line style.

        Returns a member of :ref:`MsoLineDashStyle` indicating line style, or
        |None| if no explicit value has been set. When no explicit value has
        been set, the line dash style is inherited from the style hierarchy.

        Assigning |None| removes any existing explicitly-defined dash style.
        """
        ln = self._ln
        if ln is None:
            return None
        return ln.prstDash_val

    @dash_style.setter
    def dash_style(self, dash_style):
        if dash_style is None:
            ln = self._ln
            if ln is None:
                return
            ln._remove_prstDash()
            ln._remove_custDash()
            return
        ln = self._get_or_add_ln()
        ln.prstDash_val = dash_style

    @lazyproperty
    def fill(self):
        """
        |FillFormat| instance for this line, providing access to fill
        properties such as foreground color.
        """
        ln = self._get_or_add_ln()
        return FillFormat.from_fill_parent(ln)

    @property
    def width(self):
        """
        The width of the line expressed as an integer number of :ref:`English
        Metric Units <EMU>`. The returned value is an instance of |Length|,
        a value class having properties such as `.inches`, `.cm`, and `.pt`
        for converting the value into convenient units.
        """
        ln = self._ln
        if ln is None:
            return Emu(0)
        return ln.w

    @width.setter
    def width(self, emu):
        if emu is None:
            emu = 0
        ln = self._get_or_add_ln()
        ln.w = emu

    def _get_or_add_ln(self):
        """
        Return the ``<a:ln>`` element containing the line format properties
        in the XML.
        """
        return self._parent.get_or_add_ln()

    @property
    def _ln(self):
        return self._parent.ln

    def _to_dict_properties(
        self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
    ):
        """Return a dictionary of LineFormat properties for introspection.

        Returns properties including fill, width, and dash_style.
        Leverages FillFormat.to_dict() from FEP-005 for comprehensive fill introspection.
        """
        props = {}

        # Line Fill - use FillFormat.to_dict() from FEP-005
        # This handles all fill types (SOLID, GRADIENT, PATTERN, PICTURE, BACKGROUND)
        try:
            props["fill"] = self.fill.to_dict(
                include_relationships=True,
                max_depth=max_depth - 1,
                include_private=include_private,
                expand_collections=expand_collections,
                format_for_llm=format_for_llm,
                _visited_ids=_visited_ids,
            )
        except Exception as e:
            props["fill"] = self._create_error_context("fill", e, "fill access failed")

        # Line Width (Length object)
        try:
            props["width"] = self._format_property_value_for_to_dict(
                self.width,
                include_private,
                _visited_ids,
                max_depth,
                expand_collections,
                format_for_llm,
            )
        except Exception as e:
            props["width"] = self._create_error_context("width", e, "width access failed")

        # Dash Style (MSO_LINE_DASH_STYLE enum)
        try:
            props["dash_style"] = self._format_property_value_for_to_dict(
                self.dash_style,
                include_private,
                _visited_ids,
                max_depth,
                expand_collections,
                format_for_llm,
            )
        except Exception as e:
            props["dash_style"] = self._create_error_context(
                "dash_style", e, "dash_style access failed"
            )

        return props

    def _to_dict_llm_context(
        self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private
    ):
        """Return LLM-friendly context about this LineFormat.

        Provides human-readable summary of line appearance and common operations.
        """
        context = {"description": "Describes the line (outline/border) style of an element."}

        # Generate summary based on line properties
        summary_parts = []

        try:
            line_fill_type = self.fill.type
            line_width_pt = self.width.pt if self.width else 0
            dash_style_name = self.dash_style.name if self.dash_style else "SOLID"

            # Determine if line is effectively "no line"
            if (
                line_fill_type == MSO_FILL.BACKGROUND
                or line_fill_type is None
                or line_width_pt == 0
            ):
                summary_parts.append("No line (transparent or zero width).")

            elif line_fill_type == MSO_FILL.SOLID:
                # Get color summary from fill's structured data (more robust than string parsing)
                try:
                    fill_dict = self.fill.to_dict(
                        max_depth=2, format_for_llm=True, _visited_ids=_visited_ids
                    )

                    # Extract color summary directly from structured data
                    color_summary = "solid color"  # Default fallback

                    # Check if this is indeed a solid fill and get fore_color
                    fill_props = fill_dict.get("properties", {})
                    fill_type = fill_props.get("type", {})
                    if isinstance(fill_type, dict) and fill_type.get("name") == "SOLID":
                        fore_color = fill_props.get("fore_color")
                        if fore_color and isinstance(fore_color, dict):
                            # Try to get color summary from fore_color's LLM context
                            fore_color_context = fore_color.get("_llm_context", {})
                            if fore_color_context.get("summary"):
                                color_summary = fore_color_context["summary"]
                            else:
                                # Fallback: construct summary from RGB or other color properties
                                rgb_info = fore_color.get("properties", {}).get("rgb")
                                if rgb_info and isinstance(rgb_info, dict):
                                    hex_val = rgb_info.get("hex", "unknown")
                                    color_summary = f"RGB color #{hex_val}"

                    # If color_summary still contains "color:" or similar, clean it up
                    if color_summary.endswith("."):
                        color_summary = color_summary.rstrip(".")

                    if dash_style_name == "SOLID":
                        summary_parts.append(
                            f"Solid line, {line_width_pt:.2f}pt, with {color_summary}."
                        )
                    else:
                        summary_parts.append(
                            f"{dash_style_name} line, {line_width_pt:.2f}pt, with {color_summary}."
                        )
                except Exception:
                    # Fallback if fill introspection fails
                    summary_parts.append(f"{dash_style_name} solid line, {line_width_pt:.2f}pt.")

            elif line_fill_type == MSO_FILL.GRADIENT:
                summary_parts.append(f"{dash_style_name} gradient line, {line_width_pt:.2f}pt.")

            elif line_fill_type == MSO_FILL.PICTURE:
                summary_parts.append(
                    f"{dash_style_name} picture-filled line, {line_width_pt:.2f}pt."
                )

            elif line_fill_type == MSO_FILL.PATTERNED:
                try:
                    pattern_name = self.fill.pattern.name if self.fill.pattern else "patterned"
                    summary_parts.append(
                        f"{dash_style_name} {pattern_name} patterned line, {line_width_pt:.2f}pt."
                    )
                except Exception:
                    summary_parts.append(
                        f"{dash_style_name} patterned line, {line_width_pt:.2f}pt."
                    )

            else:
                # Fallback for unknown fill types
                fill_type_name = line_fill_type.name if line_fill_type else "unknown"
                summary_parts.append(
                    f"{dash_style_name} line of type {fill_type_name}, {line_width_pt:.2f}pt."
                )

        except Exception as e:
            # Robust fallback for any errors
            summary_parts.append(f"Line formatting (error in analysis: {str(e)}).")

        context["summary"] = (
            " ".join(summary_parts) if summary_parts else "Line formatting information."
        )

        context["common_operations"] = [
            "set line color (line.color.rgb = RGBColor(...))",
            "set line width (line.width = Pt(...))",
            "set dash style (line.dash_style = MSO_LINE.DASH)",
            "remove line (line.fill.background())",
            "set solid fill (line.fill.solid())",
        ]

        return context
