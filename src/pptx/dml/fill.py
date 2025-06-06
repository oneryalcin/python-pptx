"""DrawingML objects related to fill."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from pptx.dml.color import ColorFormat
from pptx.enum.dml import MSO_FILL
from pptx.introspection import IntrospectionMixin
from pptx.oxml.dml.fill import (
    CT_BlipFillProperties,
    CT_GradientFillProperties,
    CT_GroupFillProperties,
    CT_NoFillProperties,
    CT_PatternFillProperties,
    CT_SolidColorFillProperties,
)
from pptx.oxml.xmlchemy import BaseOxmlElement
from pptx.shared import ElementProxy
from pptx.util import lazyproperty

if TYPE_CHECKING:
    from pptx.enum.dml import MSO_FILL_TYPE
    from pptx.oxml.xmlchemy import BaseOxmlElement


class FillFormat(IntrospectionMixin):
    """Provides access to the current fill properties.

    Also provides methods to change the fill type.
    """

    def __init__(self, eg_fill_properties_parent: BaseOxmlElement, fill_obj: _Fill):
        super(FillFormat, self).__init__()
        self._xPr = eg_fill_properties_parent
        self._fill = fill_obj

    @classmethod
    def from_fill_parent(cls, eg_fillProperties_parent: BaseOxmlElement) -> FillFormat:
        """
        Return a |FillFormat| instance initialized to the settings contained
        in *eg_fillProperties_parent*, which must be an element having
        EG_FillProperties in its child element sequence in the XML schema.
        """
        fill_elm = eg_fillProperties_parent.eg_fillProperties
        fill = _Fill(fill_elm)
        fill_format = cls(eg_fillProperties_parent, fill)
        return fill_format

    @property
    def back_color(self):
        """Return a |ColorFormat| object representing background color.

        This property is only applicable to pattern fills and lines.
        """
        return self._fill.back_color

    def background(self):
        """
        Sets the fill type to noFill, i.e. transparent.
        """
        noFill = self._xPr.get_or_change_to_noFill()
        self._fill = _NoFill(noFill)

    @property
    def fore_color(self):
        """
        Return a |ColorFormat| instance representing the foreground color of
        this fill.
        """
        return self._fill.fore_color

    @property
    def rId(self):
        return self._fill.rId

    @rId.setter
    def rId(self, value):
        self._fill.rId = value

    def gradient(self):
        """Sets the fill type to gradient.

        If the fill is not already a gradient, a default gradient is added.
        The default gradient corresponds to the default in the built-in
        PowerPoint "White" template. This gradient is linear at angle
        90-degrees (upward), with two stops. The first stop is Accent-1 with
        tint 100%, shade 100%, and satMod 130%. The second stop is Accent-1
        with tint 50%, shade 100%, and satMod 350%.
        """
        gradFill = self._xPr.get_or_change_to_gradFill()
        self._fill = _GradFill(gradFill)

    @property
    def gradient_angle(self):
        """Angle in float degrees of line of a linear gradient.

        Read/Write. May be |None|, indicating the angle should be inherited
        from the style hierarchy. An angle of 0.0 corresponds to
        a left-to-right gradient. Increasing angles represent
        counter-clockwise rotation of the line, for example 90.0 represents
        a bottom-to-top gradient. Raises |TypeError| when the fill type is
        not MSO_FILL_TYPE.GRADIENT. Raises |ValueError| for a non-linear
        gradient (e.g. a radial gradient).
        """
        if self.type != MSO_FILL.GRADIENT:
            raise TypeError("Fill is not of type MSO_FILL_TYPE.GRADIENT")
        return self._fill.gradient_angle

    @gradient_angle.setter
    def gradient_angle(self, value):
        if self.type != MSO_FILL.GRADIENT:
            raise TypeError("Fill is not of type MSO_FILL_TYPE.GRADIENT")
        self._fill.gradient_angle = value

    @property
    def gradient_stops(self):
        """|GradientStops| object providing access to stops of this gradient.

        Raises |TypeError| when fill is not gradient (call `fill.gradient()`
        first). Each stop represents a color between which the gradient
        smoothly transitions.
        """
        if self.type != MSO_FILL.GRADIENT:
            raise TypeError("Fill is not of type MSO_FILL_TYPE.GRADIENT")
        return self._fill.gradient_stops

    @property
    def pattern(self):
        """Return member of :ref:`MsoPatternType` indicating fill pattern.

        Raises |TypeError| when fill is not patterned (call
        `fill.patterned()` first). Returns |None| if no pattern has been set;
        PowerPoint may display the default `PERCENT_5` pattern in this case.
        Assigning |None| will remove any explicit pattern setting, although
        relying on the default behavior is discouraged and may produce
        rendering differences across client applications.
        """
        return self._fill.pattern

    @pattern.setter
    def pattern(self, pattern_type):
        self._fill.pattern = pattern_type

    def patterned(self):
        """Selects the pattern fill type.

        Note that calling this method does not by itself set a foreground or
        background color of the pattern. Rather it enables subsequent
        assignments to properties like fore_color to set the pattern and
        colors.
        """
        pattFill = self._xPr.get_or_change_to_pattFill()
        self._fill = _PattFill(pattFill)

    def solid(self):
        """
        Sets the fill type to solid, i.e. a solid color. Note that calling
        this method does not set a color or by itself cause the shape to
        appear with a solid color fill; rather it enables subsequent
        assignments to properties like fore_color to set the color.
        """
        solidFill = self._xPr.get_or_change_to_solidFill()
        self._fill = _SolidFill(solidFill)

    def blip(self):
        """
        Sets the fill type to blip, i.e. an image. Note that calling
        this method does not set an image or by itself cause the shape to
        appear with an image fill; rather it enables subsequent
        assignments to properties like rId to set the image.
        """
        blipFill = self._xPr.get_or_change_to_blipFill()
        self._fill = _BlipFill(blipFill)

    @property
    def type(self) -> MSO_FILL_TYPE:
        """The type of this fill, e.g. `MSO_FILL_TYPE.SOLID`."""
        return self._fill.type

    @property
    def value(self):
        """Return a value appropriate to the fill type.

        For solid fills, returns the foreground color.
        For pattern fills, returns the pattern type.
        For gradient fills, returns the gradient stops.
        For picture fills, returns "Picture".
        For group fills, returns "Group".
        For background (no fill), returns "Background".
        Returns None if no fill is applied.
        """
        if self.type == MSO_FILL.SOLID:
            return self.fore_color.value
        elif self.type == MSO_FILL.PATTERNED or self.type == MSO_FILL.TEXTURED:
            return "Texture"
        elif self.type == MSO_FILL.GRADIENT:
            return "GradientColor"
        elif self.type == MSO_FILL.PICTURE:
            return "Picture:rId" + str(self._fill.rId)
        return None

    # -- IntrospectionMixin overrides --

    def _to_dict_identity(
        self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private
    ):
        """Override to provide fill-specific identity information."""
        identity = super()._to_dict_identity(
            _visited_ids, max_depth, expand_collections, format_for_llm, include_private
        )
        identity["description"] = "Represents the fill formatting of an object."
        return identity

    def _to_dict_properties(
        self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
    ):
        """Override to expose fill type and type-specific properties."""
        props = {}

        # Fill type (MSO_FILL enum or None)
        fill_type_val = self.type
        props["type"] = self._format_property_value_for_to_dict(
            fill_type_val,
            include_private,
            _visited_ids,
            max_depth,
            expand_collections,
            format_for_llm,
        )

        # Type-specific properties
        if fill_type_val == MSO_FILL.SOLID:
            # Solid fill: fore_color only
            try:
                props["fore_color"] = self._format_property_value_for_to_dict(
                    self.fore_color,
                    include_private,
                    _visited_ids,
                    max_depth - 1,
                    expand_collections,
                    format_for_llm,
                )
            except (TypeError, RuntimeError, AttributeError, ValueError):
                props["fore_color"] = None
            props["back_color"] = None
            props["pattern"] = None
            props["gradient_stops"] = None
            props["gradient_angle"] = None
            props["image_rId"] = None

        elif fill_type_val in (MSO_FILL.PATTERNED, MSO_FILL.TEXTURED):
            # Pattern/texture fill: fore_color, back_color, pattern
            try:
                props["fore_color"] = self._format_property_value_for_to_dict(
                    self.fore_color,
                    include_private,
                    _visited_ids,
                    max_depth - 1,
                    expand_collections,
                    format_for_llm,
                )
            except (TypeError, RuntimeError, AttributeError, ValueError):
                props["fore_color"] = None
            try:
                props["back_color"] = self._format_property_value_for_to_dict(
                    self.back_color,
                    include_private,
                    _visited_ids,
                    max_depth - 1,
                    expand_collections,
                    format_for_llm,
                )
            except (TypeError, RuntimeError, AttributeError, ValueError):
                props["back_color"] = None
            try:
                props["pattern"] = self._format_property_value_for_to_dict(
                    self.pattern,
                    include_private,
                    _visited_ids,
                    max_depth,
                    expand_collections,
                    format_for_llm,
                )
            except (TypeError, RuntimeError, AttributeError, ValueError):
                props["pattern"] = None
            props["gradient_stops"] = None
            props["gradient_angle"] = None
            props["image_rId"] = None

        elif fill_type_val == MSO_FILL.GRADIENT:
            # Gradient fill: gradient_stops, gradient_angle
            try:
                gradient_stops = self.gradient_stops
                if expand_collections and max_depth > 0:
                    props["gradient_stops"] = [
                        stop.to_dict(
                            include_relationships=False,
                            max_depth=max_depth - 1,
                            include_private=include_private,
                            expand_collections=expand_collections,
                            format_for_llm=format_for_llm,
                            _visited_ids=_visited_ids,
                        )
                        for stop in gradient_stops
                    ]
                else:
                    props["gradient_stops"] = (
                        f"Collection of {len(gradient_stops)} gradient stops "
                        f"(not expanded due to max_depth or expand_collections=False)"
                    )
            except (TypeError, RuntimeError, AttributeError, ValueError):
                props["gradient_stops"] = None

            try:
                props["gradient_angle"] = self.gradient_angle
            except (TypeError, ValueError):
                # ValueError for non-linear gradients, TypeError for wrong fill type
                props["gradient_angle"] = None

            props["fore_color"] = None
            props["back_color"] = None
            props["pattern"] = None
            props["image_rId"] = None

        elif fill_type_val == MSO_FILL.PICTURE:
            # Picture fill: image_rId
            try:
                props["image_rId"] = self.rId
            except (TypeError, AttributeError):
                props["image_rId"] = None
            props["fore_color"] = None
            props["back_color"] = None
            props["pattern"] = None
            props["gradient_stops"] = None
            props["gradient_angle"] = None

        else:
            # For BACKGROUND, GROUP, or None types
            props["fore_color"] = None
            props["back_color"] = None
            props["pattern"] = None
            props["gradient_stops"] = None
            props["gradient_angle"] = None
            props["image_rId"] = None

        return props

    def _to_dict_relationships(
        self, remaining_depth, expand_collections, _visited_ids, format_for_llm, include_private
    ):
        """Override to include picture fill relationships if applicable."""
        rels = {}

        if self.type == MSO_FILL.PICTURE and remaining_depth > 0:
            try:
                rId = self.rId
                if rId and hasattr(self._xPr, "part"):
                    # Try to resolve the relationship to the actual image part
                    try:
                        image_part = self._xPr.part.related_part(rId)
                        if hasattr(image_part, "to_dict"):
                            rels["image_part"] = image_part.to_dict(
                                max_depth=0,
                                _visited_ids=_visited_ids,
                                include_relationships=False,
                                expand_collections=False,
                                include_private=include_private,
                                format_for_llm=format_for_llm,
                            )
                        else:
                            rels["image_part_ref"] = repr(image_part)
                    except Exception as e:
                        rels["image_part_error"] = self._create_error_context(
                            "image_part_resolution", e, rId
                        )
                elif rId:
                    rels["image_rId_only"] = rId
            except Exception as e:
                rels["image_relationship_error"] = self._create_error_context(
                    "image_relationship", e, None
                )

        return rels

    def _to_dict_llm_context(
        self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private
    ):
        """Override to provide fill-specific LLM context with human-readable descriptions."""
        context = {"description": "Describes the fill style of an element."}
        fill_type_val = self.type
        summary_parts = []

        if fill_type_val == MSO_FILL.SOLID:
            try:
                fc_dict = self.fore_color.to_dict(
                    max_depth=0,
                    format_for_llm=True,
                    _visited_ids=_visited_ids,
                    include_relationships=False,
                    expand_collections=False,
                    include_private=False,
                )
                color_summary = fc_dict.get("_llm_context", {}).get("summary", "color")
                summary_parts.append(f"Solid fill with {color_summary}")
            except (TypeError, AttributeError, RuntimeError, ValueError):
                summary_parts.append("Solid fill (color details unavailable)")

        elif fill_type_val in (MSO_FILL.PATTERNED, MSO_FILL.TEXTURED):
            fill_type_name = "Patterned" if fill_type_val == MSO_FILL.PATTERNED else "Textured"
            try:
                pattern_name = self.pattern.name if self.pattern else "Default"
                summary_parts.append(f"{fill_type_name} fill: {pattern_name}")
            except (TypeError, AttributeError, RuntimeError, ValueError):
                summary_parts.append(f"{fill_type_name} fill")

        elif fill_type_val == MSO_FILL.GRADIENT:
            try:
                stop_count = len(self.gradient_stops)
                angle_desc = ""
                try:
                    angle = self.gradient_angle
                    if angle is not None:
                        angle_desc = f" at {angle:.0f} degrees"
                except (ValueError, TypeError):
                    angle_desc = " (non-linear or angle unavailable)"
                summary_parts.append(f"{stop_count}-stop gradient{angle_desc}")
            except (TypeError, AttributeError, RuntimeError, ValueError):
                summary_parts.append("Gradient fill (details unavailable)")

        elif fill_type_val == MSO_FILL.PICTURE:
            try:
                rId = self.rId
                rId_info = f" (rId: {rId})" if rId else ""
                summary_parts.append(f"Picture fill{rId_info}")
            except (TypeError, AttributeError, RuntimeError, ValueError):
                summary_parts.append("Picture fill")

        elif fill_type_val == MSO_FILL.BACKGROUND:
            summary_parts.append("Background fill (transparent)")

        elif fill_type_val == MSO_FILL.GROUP:
            summary_parts.append("Group fill (inherits from group)")

        elif fill_type_val is None:
            summary_parts.append("No explicit fill defined (fill is inherited)")

        else:
            summary_parts.append(
                f"Fill of type {fill_type_val.name if fill_type_val else 'Unknown'}"
            )

        context["summary"] = " ".join(summary_parts) + "."
        context["common_operations"] = [
            "set solid color (fill.solid(), fill.fore_color = ...)",
            "set gradient (fill.gradient(), access fill.gradient_stops)",
            "set pattern (fill.patterned(), set fill.pattern)",
            "set picture (fill.blip(), set fill.rId)",
            "set no fill (fill.background())",
        ]
        return context


class _Fill(object):
    """
    Object factory for fill object of class matching fill element, such as
    _SolidFill for ``<a:solidFill>``; also serves as the base class for all
    fill classes
    """

    def __new__(cls, xFill):
        if xFill is None:
            fill_cls = _NoneFill
        elif isinstance(xFill, CT_BlipFillProperties):
            fill_cls = _BlipFill
        elif isinstance(xFill, CT_GradientFillProperties):
            fill_cls = _GradFill
        elif isinstance(xFill, CT_GroupFillProperties):
            fill_cls = _GrpFill
        elif isinstance(xFill, CT_NoFillProperties):
            fill_cls = _NoFill
        elif isinstance(xFill, CT_PatternFillProperties):
            fill_cls = _PattFill
        elif isinstance(xFill, CT_SolidColorFillProperties):
            fill_cls = _SolidFill
        else:
            fill_cls = _Fill
        return super(_Fill, cls).__new__(fill_cls)

    @property
    def back_color(self):
        """Raise TypeError for types that do not override this property."""
        tmpl = "fill type %s has no background color, call .patterned() first"
        raise TypeError(tmpl % self.__class__.__name__)

    @property
    def fore_color(self):
        """Raise TypeError for types that do not override this property."""
        tmpl = "fill type %s has no foreground color, call .solid() or .patterned() first"
        raise TypeError(tmpl % self.__class__.__name__)

    @property
    def pattern(self):
        """Raise TypeError for fills that do not override this property."""
        tmpl = "fill type %s has no pattern, call .patterned() first"
        raise TypeError(tmpl % self.__class__.__name__)

    @property
    def type(self) -> MSO_FILL_TYPE:  # pragma: no cover
        raise NotImplementedError(
            f".type property must be implemented on {self.__class__.__name__}"
        )

    @property
    def rId(self):
        raise NotImplementedError(f".rId property must be implemented on {self.__class__.__name__}")


class _BlipFill(_Fill):
    def __init__(self, blipFill: CT_BlipFillProperties):
        self._blipFill = blipFill

    @property
    def type(self):
        return MSO_FILL.PICTURE

    @property
    def rId(self):
        if not hasattr(self._blipFill, "blip") or self._blipFill.blip is None:
            return None
        return self._blipFill.blip.rEmbed

    @rId.setter
    def rId(self, value):
        blip = self._blipFill.get_or_add_blip()
        blip.rEmbed = value


class _GradFill(_Fill):
    """Proxies an `a:gradFill` element."""

    def __init__(self, gradFill):
        self._element = self._gradFill = gradFill

    @property
    def gradient_angle(self):
        """Angle in float degrees of line of a linear gradient.

        Read/Write. May be |None|, indicating the angle is inherited from the
        style hierarchy. An angle of 0.0 corresponds to a left-to-right
        gradient. Increasing angles represent clockwise rotation of the line,
        for example 90.0 represents a top-to-bottom gradient. Raises
        |TypeError| when the fill type is not MSO_FILL_TYPE.GRADIENT. Raises
        |ValueError| for a non-linear gradient (e.g. a radial gradient).
        """
        # ---case 1: gradient path is explicit, but not linear---
        path = self._gradFill.path
        if path is not None:
            raise ValueError("not a linear gradient")

        # ---case 2: gradient path is inherited (no a:lin OR a:path)---
        lin = self._gradFill.lin
        if lin is None:
            return None

        # ---case 3: gradient path is explicitly linear---
        # angle is stored in XML as a clockwise angle, whereas the UI
        # reports it as counter-clockwise from horizontal-pointing-right.
        # Since the UI is consistent with trigonometry conventions, we
        # respect that in the API.
        clockwise_angle = lin.ang
        counter_clockwise_angle = 0.0 if clockwise_angle == 0.0 else (360.0 - clockwise_angle)
        return counter_clockwise_angle

    @gradient_angle.setter
    def gradient_angle(self, value):
        lin = self._gradFill.lin
        if lin is None:
            raise ValueError("not a linear gradient")
        lin.ang = 360.0 - value

    @lazyproperty
    def gradient_stops(self):
        """|_GradientStops| object providing access to gradient colors.

        Each stop represents a color between which the gradient smoothly
        transitions.
        """
        return _GradientStops(self._gradFill.get_or_add_gsLst())

    @property
    def type(self):
        return MSO_FILL.GRADIENT


class _GrpFill(_Fill):
    @property
    def type(self):
        return MSO_FILL.GROUP


class _NoFill(_Fill):
    @property
    def type(self):
        return MSO_FILL.BACKGROUND


class _NoneFill(_Fill):
    @property
    def type(self):
        return None


class _PattFill(_Fill):
    """Provides access to patterned fill properties."""

    def __init__(self, pattFill):
        super(_PattFill, self).__init__()
        self._element = self._pattFill = pattFill

    @lazyproperty
    def back_color(self):
        """Return |ColorFormat| object that controls background color."""
        bgClr = self._pattFill.get_or_add_bgClr()
        return ColorFormat.from_colorchoice_parent(bgClr)

    @lazyproperty
    def fore_color(self):
        """Return |ColorFormat| object that controls foreground color."""
        fgClr = self._pattFill.get_or_add_fgClr()
        return ColorFormat.from_colorchoice_parent(fgClr)

    @property
    def pattern(self):
        """Return member of :ref:`MsoPatternType` indicating fill pattern.

        Returns |None| if no pattern has been set; PowerPoint may display the
        default `PERCENT_5` pattern in this case. Assigning |None| will
        remove any explicit pattern setting.
        """
        return self._pattFill.prst

    @pattern.setter
    def pattern(self, pattern_type):
        self._pattFill.prst = pattern_type

    @property
    def type(self):
        return MSO_FILL.PATTERNED


class _SolidFill(_Fill):
    """Provides access to fill properties such as color for solid fills."""

    def __init__(self, solidFill):
        super(_SolidFill, self).__init__()
        self._solidFill = solidFill

    @lazyproperty
    def fore_color(self):
        """Return |ColorFormat| object controlling fill color."""
        return ColorFormat.from_colorchoice_parent(self._solidFill)

    @property
    def type(self):
        return MSO_FILL.SOLID


class _GradientStops(Sequence):
    """Collection of |GradientStop| objects defining gradient colors.

    A gradient must have a minimum of two stops, but can have as many more
    than that as required to achieve the desired effect (three is perhaps
    most common). Stops are sequenced in the order they are transitioned
    through.
    """

    def __init__(self, gsLst):
        self._gsLst = gsLst

    def __getitem__(self, idx):
        return _GradientStop(self._gsLst[idx])

    def __len__(self):
        return len(self._gsLst)


class _GradientStop(ElementProxy, IntrospectionMixin):
    """A single gradient stop.

    A gradient stop defines a color and a position.
    """

    def __init__(self, gs):
        super(_GradientStop, self).__init__(gs)
        self._gs = gs

    @lazyproperty
    def color(self):
        """Return |ColorFormat| object controlling stop color."""
        return ColorFormat.from_colorchoice_parent(self._gs)

    @property
    def position(self):
        """Location of stop in gradient path as float between 0.0 and 1.0.

        The value represents a percentage, where 0.0 (0%) represents the
        start of the path and 1.0 (100%) represents the end of the path. For
        a linear gradient, these would represent opposing extents of the
        filled area.
        """
        return self._gs.pos

    @position.setter
    def position(self, value):
        self._gs.pos = float(value)

    # -- IntrospectionMixin overrides --

    def _to_dict_identity(
        self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private
    ):
        """Override to provide gradient stop-specific identity information."""
        identity = super()._to_dict_identity(
            _visited_ids, max_depth, expand_collections, format_for_llm, include_private
        )
        identity["description"] = "Represents a color stop in a gradient."
        return identity

    def _to_dict_properties(
        self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
    ):
        """Override to expose position and color properties."""
        props = {}

        # Position (float between 0.0 and 1.0)
        props["position"] = self.position

        # Color (ColorFormat object)
        props["color"] = self._format_property_value_for_to_dict(
            self.color,
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
        """Override to include minimal relationships.

        GradientStop typically doesn't own other complex objects.
        """
        return {}

    def _to_dict_llm_context(
        self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private
    ):
        """Override to provide gradient stop-specific LLM context.

        Provides human-readable descriptions for gradient stops.
        """
        context = {"description": "Represents a color stop in a gradient."}

        try:
            position_pct = self.position * 100
            color_dict = self.color.to_dict(
                max_depth=0,
                format_for_llm=True,
                _visited_ids=_visited_ids,
                include_relationships=False,
                expand_collections=False,
                include_private=False,
            )
            color_summary = color_dict.get("_llm_context", {}).get("summary", "color")
            context["summary"] = (
                f"Gradient stop at {position_pct:.0f}% position with {color_summary}"
            )
        except (AttributeError, TypeError):
            context["summary"] = f"Gradient stop at position {self.position:.2f}"

        context["common_operations"] = [
            "adjust position (stop.position = 0.5)",
            "change color (stop.color.rgb = RGBColor(...))",
        ]
        return context
