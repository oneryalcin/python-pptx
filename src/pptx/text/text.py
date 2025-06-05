"""Text-related objects such as TextFrame and Paragraph."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Iterator, cast

from lxml import etree

from pptx.dml.fill import FillFormat
from pptx.enum.lang import MSO_LANGUAGE_ID
from pptx.enum.text import MSO_AUTO_SIZE, MSO_UNDERLINE, MSO_VERTICAL_ANCHOR
from pptx.introspection import IntrospectionMixin
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml.simpletypes import ST_TextFontStrike, ST_TextWrappingType
from pptx.shapes import Subshape
from pptx.text.fonts import FontFiles
from pptx.text.layout import TextFitter
from pptx.util import Centipoints, Emu, Length, Pt, lazyproperty

if TYPE_CHECKING:
    from pptx.enum.text import (
        MSO_TEXT_UNDERLINE_TYPE,
        MSO_VERTICAL_ANCHOR,
        PP_PARAGRAPH_ALIGNMENT,
    )
    from pptx.oxml.action import CT_Hyperlink
    from pptx.oxml.text import (
        CT_RegularTextRun,
        CT_TextBody,
        CT_TextCharacterProperties,
        CT_TextParagraph,
        CT_TextParagraphProperties,
    )
    from pptx.types import ProvidesExtents, ProvidesPart


class TextFrame(Subshape, IntrospectionMixin):
    """The part of a shape that contains its text.

    Not all shapes have a text frame. Corresponds to the `p:txBody` element that can
    appear as a child element of `p:sp`. Not intended to be constructed directly.
    """

    def __init__(self, txBody: CT_TextBody, parent: ProvidesPart):
        super(TextFrame, self).__init__(parent)
        IntrospectionMixin.__init__(self)
        self._element = self._txBody = txBody
        self._parent = parent

    def add_paragraph(self):
        """
        Return new |_Paragraph| instance appended to the sequence of
        paragraphs contained in this text frame.
        """
        p = self._txBody.add_p()
        return _Paragraph(p, self)

    @property
    def auto_size(self) -> MSO_AUTO_SIZE | None:
        """Resizing strategy used to fit text within this shape.

        Determins the type of automatic resizing used to fit the text of this shape within its
        bounding box when the text would otherwise extend beyond the shape boundaries. May be
        |None|, `MSO_AUTO_SIZE.NONE`, `MSO_AUTO_SIZE.SHAPE_TO_FIT_TEXT`, or
        `MSO_AUTO_SIZE.TEXT_TO_FIT_SHAPE`.
        """
        return self._bodyPr.autofit

    @auto_size.setter
    def auto_size(self, value: MSO_AUTO_SIZE | None):
        self._bodyPr.autofit = value

    def clear(self):
        """Remove all paragraphs except one empty one."""
        for p in self._txBody.p_lst[1:]:
            self._txBody.remove(p)
        p = self.paragraphs[0]
        p.clear()

    def fit_text(
        self,
        font_family: str = "Calibri",
        max_size: int = 18,
        bold: bool = False,
        italic: bool = False,
        font_file: str | None = None,
    ):
        """Fit text-frame text entirely within bounds of its shape.

        Make the text in this text frame fit entirely within the bounds of its shape by setting
        word wrap on and applying the "best-fit" font size to all the text it contains.

        :attr:`TextFrame.auto_size` is set to :attr:`MSO_AUTO_SIZE.NONE`. The font size will not
        be set larger than `max_size` points. If the path to a matching TrueType font is provided
        as `font_file`, that font file will be used for the font metrics. If `font_file` is |None|,
        best efforts are made to locate a font file with matchhing `font_family`, `bold`, and
        `italic` installed on the current system (usually succeeds if the font is installed).
        """
        # ---no-op when empty as fit behavior not defined for that case---
        if self.text == "":
            return  # pragma: no cover

        font_size = self._best_fit_font_size(font_family, max_size, bold, italic, font_file)
        self._apply_fit(font_family, font_size, bold, italic)

    @property
    def margin_bottom(self) -> Length:
        """|Length| value representing the inset of text from the bottom text frame border.

        :meth:`pptx.util.Inches` provides a convenient way of setting the value, e.g.
        `text_frame.margin_bottom = Inches(0.05)`.
        """
        return self._bodyPr.bIns

    @margin_bottom.setter
    def margin_bottom(self, emu: Length):
        self._bodyPr.bIns = emu

    @property
    def margin_left(self) -> Length:
        """Inset of text from left text frame border as |Length| value."""
        return self._bodyPr.lIns

    @margin_left.setter
    def margin_left(self, emu: Length):
        self._bodyPr.lIns = emu

    @property
    def margin_right(self) -> Length:
        """Inset of text from right text frame border as |Length| value."""
        return self._bodyPr.rIns

    @margin_right.setter
    def margin_right(self, emu: Length):
        self._bodyPr.rIns = emu

    @property
    def margin_top(self) -> Length:
        """Inset of text from top text frame border as |Length| value."""
        return self._bodyPr.tIns

    @margin_top.setter
    def margin_top(self, emu: Length):
        self._bodyPr.tIns = emu

    @property
    def paragraphs(self) -> tuple[_Paragraph, ...]:
        """Sequence of paragraphs in this text frame.

        A text frame always contains at least one paragraph.
        """
        return tuple([_Paragraph(p, self) for p in self._txBody.p_lst])

    @property
    def text(self) -> str:
        """All text in this text-frame as a single string.

        Read/write. The return value contains all text in this text-frame. A line-feed character
        (`"\\n"`) separates the text for each paragraph. A vertical-tab character (`"\\v"`) appears
        for each line break (aka. soft carriage-return) encountered.

        The vertical-tab character is how PowerPoint represents a soft carriage return in clipboard
        text, which is why that encoding was chosen.

        Assignment replaces all text in the text frame. A new paragraph is added for each line-feed
        character (`"\\n"`) encountered. A line-break (soft carriage-return) is inserted for each
        vertical-tab character (`"\\v"`) encountered.

        Any control character other than newline, tab, or vertical-tab are escaped as plain-text
        like "_x001B_" (for ESC (ASCII 32) in this example).
        """
        return "\n".join(paragraph.text for paragraph in self.paragraphs)

    @text.setter
    def text(self, text: str):
        txBody = self._txBody
        txBody.clear_content()
        for p_text in text.split("\n"):
            p = txBody.add_p()
            p.append_text(p_text)

    @property
    def alignment(self) -> PP_PARAGRAPH_ALIGNMENT | None:
        """Horizontal alignment of this paragraph.

        The value |None| indicates the paragraph should 'inherit' its effective value from its
        style hierarchy. Assigning |None| removes any explicit setting, causing its inherited
        value to be used.
        """
        lv1bPr = getattr(self._txBody.lstStyle, "lv1bPr", None)
        if lv1bPr is None:
            return None
        return lv1bPr.algn

    @alignment.setter
    def alignment(self, value: PP_PARAGRAPH_ALIGNMENT | None):
        lv1bPr = self._txBody.lstStyle.get_or_add_lv1bPr()
        lv1bPr.algn = value

    @property
    def level(self) -> int:
        """Indentation level of this paragraph.

        Read-write. Integer in range 0..8 inclusive. 0 represents a top-level paragraph and is the
        default value. Indentation level is most commonly encountered in a bulleted list, as is
        found on a word bullet slide.
        """
        lv1bPr = getattr(self._txBody.lstStyle, "lv1bPr", None)
        if lv1bPr is None:
            return 0  # Default level
        return lv1bPr.lvl

    @level.setter
    def level(self, level: int):
        lv1bPr = self._txBody.lstStyle.get_or_add_lv1bPr()
        lv1bPr.lvl = level

    @property
    def font(self) -> Font:
        """|Font| object containing default character properties for the runs in this paragraph.

        These character properties override default properties inherited from parent objects such
        as the text frame the paragraph is contained in and they may be overridden by character
        properties set at the run level.
        """
        return Font(self._defRPr)

    @property
    def vertical_anchor(self) -> MSO_VERTICAL_ANCHOR | None:
        """Represents the vertical alignment of text in this text frame.

        |None| indicates the effective value should be inherited from this object's style hierarchy.
        """
        return self._txBody.bodyPr.anchor

    @vertical_anchor.setter
    def vertical_anchor(self, value: MSO_VERTICAL_ANCHOR | None):
        bodyPr = self._txBody.bodyPr
        bodyPr.anchor = value

    @property
    def word_wrap(self) -> bool | None:
        """`True` when lines of text in this shape are wrapped to fit within the shape's width.

        Read-write. Valid values are True, False, or None. True and False turn word wrap on and
        off, respectively. Assigning None to word wrap causes any word wrap setting to be removed
        from the text frame, causing it to inherit this setting from its style hierarchy.
        """
        return {
            ST_TextWrappingType.SQUARE: True,
            ST_TextWrappingType.NONE: False,
            None: None,
        }[self._txBody.bodyPr.wrap]

    @word_wrap.setter
    def word_wrap(self, value: bool | None):
        if value not in (True, False, None):
            raise ValueError(  # pragma: no cover
                "assigned value must be True, False, or None, got %s" % value
            )
        self._txBody.bodyPr.wrap = {
            True: ST_TextWrappingType.SQUARE,
            False: ST_TextWrappingType.NONE,
            None: None,
        }[value]

    # -- IntrospectionMixin overrides --

    def _to_dict_identity(
        self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private
    ):
        """Override to provide text frame-specific identity information."""
        identity = super()._to_dict_identity(
            _visited_ids, max_depth, expand_collections, format_for_llm, include_private
        )
        identity["description"] = "Container for text within a shape."

        # Add parent shape info if available
        if self._parent and hasattr(self._parent, "name"):
            with contextlib.suppress(Exception):
                identity["parent_shape_name"] = self._parent.name

        return identity

    def _to_dict_properties(
        self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
    ):
        """Override to expose text frame properties and paragraphs."""
        props = {}

        # Full text content
        props["text"] = self.text

        # Paragraphs collection (recursive calls to FEP-010)
        try:
            if expand_collections and max_depth > 1:
                paragraphs_list = []
                for paragraph in self.paragraphs:
                    if hasattr(paragraph, "to_dict"):
                        paragraphs_list.append(
                            paragraph.to_dict(
                                include_relationships=True,
                                max_depth=max_depth - 1,
                                include_private=include_private,
                                expand_collections=expand_collections,
                                format_for_llm=format_for_llm,
                                _visited_ids=_visited_ids,
                            )
                        )
                    else:
                        paragraphs_list.append(
                            {"_object_type": "_Paragraph", "_no_introspection": True}
                        )
                props["paragraphs"] = paragraphs_list
            elif expand_collections:
                props["paragraphs"] = [
                    {"_object_type": "_Paragraph", "_depth_exceeded": True} for _ in self.paragraphs
                ]
            else:
                props["paragraphs"] = {"_collection_summary": f"{len(self.paragraphs)} paragraphs"}
        except Exception as e:
            props["paragraphs"] = self._create_error_context(
                "paragraphs", e, "paragraphs collection access failed"
            )

        # Margin properties
        margin_attrs = ["margin_left", "margin_top", "margin_right", "margin_bottom"]
        for attr_name in margin_attrs:
            try:
                attr_value = getattr(self, attr_name)
                props[attr_name] = self._format_property_value_for_to_dict(
                    attr_value,
                    include_private,
                    _visited_ids,
                    max_depth,
                    expand_collections,
                    format_for_llm,
                )
            except Exception as e:
                props[attr_name] = self._create_error_context(
                    attr_name, e, "margin property access failed"
                )

        # Text frame behavior properties
        text_frame_attrs = ["vertical_anchor", "word_wrap", "auto_size", "alignment", "level"]
        for attr_name in text_frame_attrs:
            try:
                attr_value = getattr(self, attr_name)
                props[attr_name] = self._format_property_value_for_to_dict(
                    attr_value,
                    include_private,
                    _visited_ids,
                    max_depth,
                    expand_collections,
                    format_for_llm,
                )
            except Exception as e:
                props[attr_name] = self._create_error_context(
                    attr_name, e, f"{attr_name} property access failed"
                )

        # Default font for the text frame (recursive call to FEP-007)
        try:
            if max_depth > 1:
                props["font"] = self.font.to_dict(
                    include_relationships=False,
                    max_depth=max_depth - 1,
                    include_private=include_private,
                    expand_collections=expand_collections,
                    format_for_llm=format_for_llm,
                    _visited_ids=_visited_ids,
                )
            else:
                props["font"] = {"_object_type": "Font", "_depth_exceeded": True}
        except Exception as e:
            props["font"] = self._create_error_context("font", e, "font access failed")

        return props

    def _to_dict_relationships(
        self, remaining_depth, expand_collections, _visited_ids, format_for_llm, include_private
    ):
        """Override to include parent shape relationship."""
        rels = super()._to_dict_relationships(
            remaining_depth, expand_collections, _visited_ids, format_for_llm, include_private
        )

        # Parent shape (the shape containing this text frame)
        if self._parent is not None:
            if hasattr(self._parent, "to_dict") and callable(getattr(self._parent, "to_dict")):
                try:
                    rels["parent_shape"] = self._parent.to_dict(
                        include_relationships=False,
                        max_depth=0,  # Summary only
                        include_private=include_private,
                        expand_collections=False,
                        format_for_llm=format_for_llm,
                        _visited_ids=_visited_ids,
                    )
                except Exception:
                    # Fallback to repr if to_dict fails
                    rels["parent_shape"] = repr(self._parent)
            else:
                # Fallback to repr if no to_dict method
                rels["parent_shape"] = repr(self._parent)

        return rels

    def _to_dict_llm_context(
        self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private
    ):
        """Override to provide text frame-specific LLM context."""
        context = super()._to_dict_llm_context(
            _visited_ids, max_depth, expand_collections, format_for_llm, include_private
        )

        # Build descriptive context
        try:
            text_preview = self.text[:100].replace("\n", " ").replace("\v", " ")
            if len(self.text) > 100:
                text_preview += "..."

            desc_parts = [f"TextFrame containing {len(self.paragraphs)} paragraph(s)."]
            if text_preview.strip():
                desc_parts.append(f'Text starts with: "{text_preview}".')

            # Key properties summary
            try:
                if self.auto_size is not None:
                    desc_parts.append(f"Auto-size: {self.auto_size.name}.")
            except Exception:
                pass

            try:
                if self.word_wrap is not None:
                    desc_parts.append(f"Word wrap: {'On' if self.word_wrap else 'Off'}.")
            except Exception:
                pass

            try:
                if self.vertical_anchor is not None:
                    desc_parts.append(f"Vertical anchor: {self.vertical_anchor.name}.")
            except Exception:
                pass

            context["description"] = " ".join(
                p.rstrip(".") + "." for p in desc_parts if p.rstrip(".")
            )
            context["summary"] = context["description"]

            context["common_operations"] = [
                "access/modify text (text_frame.text = ...)",
                "add paragraphs (text_frame.add_paragraph())",
                "access paragraphs (text_frame.paragraphs)",
                "set margins (text_frame.margin_left = Inches(...))",
                "set vertical anchor (text_frame.vertical_anchor = MSO_ANCHOR...)",
                "set word wrap (text_frame.word_wrap = True/False/None)",
                "set auto-size (text_frame.auto_size = MSO_AUTO_SIZE...)",
                "set default paragraph alignment/level (text_frame.alignment, text_frame.level)",
                "set default font (text_frame.font...)",
            ]

        except Exception as e:
            context["description"] = f"TextFrame with introspection error: {str(e)}"
            context["summary"] = context["description"]

        return context

    def _apply_fit(self, font_family: str, font_size: int, is_bold: bool, is_italic: bool):
        """Arrange text in this text frame to fit inside its extents.

        This is accomplished by setting auto size off, wrap on, and setting the font of
        all its text to `font_family`, `font_size`, `is_bold`, and `is_italic`.
        """
        self.auto_size = MSO_AUTO_SIZE.NONE
        self.word_wrap = True
        self._set_font(font_family, font_size, is_bold, is_italic)

    def _best_fit_font_size(
        self, family: str, max_size: int, bold: bool, italic: bool, font_file: str | None
    ) -> int:
        """Return font-size in points that best fits text in this text-frame.

        The best-fit font size is the largest integer point size not greater than `max_size` that
        allows all the text in this text frame to fit inside its extents when rendered using the
        font described by `family`, `bold`, and `italic`. If `font_file` is specified, it is used
        to calculate the fit, whether or not it matches `family`, `bold`, and `italic`.
        """
        if font_file is None:
            font_file = FontFiles.find(family, bold, italic)
        return TextFitter.best_fit_font_size(self.text, self._extents, max_size, font_file)

    @property
    def _bodyPr(self):
        return self._txBody.bodyPr

    @property
    def _extents(self) -> tuple[Length, Length]:
        """(cx, cy) 2-tuple representing the effective rendering area of this text-frame.

        Margins are taken into account.
        """
        parent = cast("ProvidesExtents", self._parent)
        return (
            Length(parent.width - self.margin_left - self.margin_right),
            Length(parent.height - self.margin_top - self.margin_bottom),
        )

    def _set_font(self, family: str, size: int, bold: bool, italic: bool):
        """Set the font properties of all the text in this text frame."""

        def iter_rPrs(txBody: CT_TextBody) -> Iterator[CT_TextCharacterProperties]:
            for p in txBody.p_lst:
                for elm in p.content_children:
                    yield elm.get_or_add_rPr()
                # generate a:endParaRPr for each <a:p> element
                yield p.get_or_add_endParaRPr()

        def set_rPr_font(
            rPr: CT_TextCharacterProperties, name: str, size: int, bold: bool, italic: bool
        ):
            f = Font(rPr)
            f.name, f.size, f.bold, f.italic = family, Pt(size), bold, italic

        txBody = self._element
        for rPr in iter_rPrs(txBody):
            set_rPr_font(rPr, family, size, bold, italic)

    @property
    def _lv1bPr(self) -> CT_TextParagraphProperties:
        return self._txBody.lstStyle.get_or_add_lv1bPr()

    @property
    def _defRPr(self) -> CT_TextCharacterProperties:
        """The element that defines the default run properties for runs in this paragraph.

        Causes the element to be added if not present.
        """
        return self._lv1bPr.get_or_add_defRPr()


class Font(IntrospectionMixin):
    """Character properties object, providing font size, font name, bold, italic, etc.

    Corresponds to `a:rPr` child element of a run. Also appears as `a:defRPr` and
    `a:endParaRPr` in paragraph and `a:defRPr` in list style elements.
    """

    def __init__(self, rPr: CT_TextCharacterProperties):
        super(Font, self).__init__()
        self._element = self._rPr = rPr

    @property
    def bold(self) -> bool | None:
        """Get or set boolean bold value of |Font|, e.g. `paragraph.font.bold = True`.

        If set to |None|, the bold setting is cleared and is inherited from an enclosing shape's
        setting, or a setting in a style or master. Returns None if no bold attribute is present,
        meaning the effective bold value is inherited from a master or the theme.
        """
        return self._rPr.b

    @bold.setter
    def bold(self, value: bool | None):
        self._rPr.b = value

    @property
    def strikethrough(self):
        return {
            ST_TextFontStrike.SINGLE_STRIKE: True,
            ST_TextFontStrike.DOUBLE_STRIKE: True,
            ST_TextFontStrike.NO_STRIKE: False,
            None: None,
        }[self._rPr.strike]

    @strikethrough.setter
    def strikethrough(self, value):
        if value not in (True, False, None):
            raise ValueError("assigned value must be True, False, or None, got %s" % value)
        self._rPr.strike = {
            True: ST_TextFontStrike.SINGLE_STRIKE,
            False: ST_TextFontStrike.NO_STRIKE,
            None: None,
        }[value]

    @lazyproperty
    def color(self) -> str | None:
        """The |ColorFormat| instance that provides access to the color settings for this font."""
        return self.fill.value

    @lazyproperty
    def fill(self) -> FillFormat:
        """|FillFormat| instance for this font.

        Provides access to fill properties such as fill color.
        """
        return FillFormat.from_fill_parent(self._rPr)

    @property
    def italic(self) -> bool | None:
        """Get or set boolean italic value of |Font| instance.

        Has the same behaviors as bold with respect to None values.
        """
        return self._rPr.i

    @italic.setter
    def italic(self, value: bool | None):
        self._rPr.i = value

    @property
    def language_id(self) -> MSO_LANGUAGE_ID | None:
        """Get or set the language id of this |Font| instance.

        The language id is a member of the :ref:`MsoLanguageId` enumeration. Assigning |None|
        removes any language setting, the same behavior as assigning `MSO_LANGUAGE_ID.NONE`.
        """
        lang = self._rPr.lang
        if lang is None:
            return MSO_LANGUAGE_ID.NONE
        return self._rPr.lang

    @language_id.setter
    def language_id(self, value: MSO_LANGUAGE_ID | None):
        if value == MSO_LANGUAGE_ID.NONE:
            value = None
        self._rPr.lang = value

    @property
    def name(self) -> str | None:
        """Get or set the typeface name for this |Font| instance.

        Causes the text it controls to appear in the named font, if a matching font is found.
        Returns |None| if the typeface is currently inherited from the theme. Setting it to |None|
        removes any override of the theme typeface.
        """
        latin = self._rPr.latin
        if latin is None:
            return None
        return latin.typeface

    @name.setter
    def name(self, value: str | None):
        if value is None:
            self._rPr._remove_latin()  # pyright: ignore[reportPrivateUsage]
        else:
            latin = self._rPr.get_or_add_latin()
            latin.typeface = value

    @property
    def size(self) -> Length | None:
        """Indicates the font height in English Metric Units (EMU).

        Read/write. |None| indicates the font size should be inherited from its style hierarchy,
        such as a placeholder or document defaults (usually 18pt). |Length| is a subclass of |int|
        having properties for convenient conversion into points or other length units. Likewise,
        the :class:`pptx.util.Pt` class allows convenient specification of point values::

            >>> font.size = Pt(24)
            >>> font.size
            304800
            >>> font.size.pt
            24.0
        """
        sz = self._rPr.sz
        if sz is None:
            return None
        return Centipoints(sz)

    @size.setter
    def size(self, emu: Length | None):
        if emu is None:
            self._rPr.sz = None
        else:
            sz = Emu(emu).centipoints
            self._rPr.sz = sz

    @property
    def underline(self) -> bool | MSO_TEXT_UNDERLINE_TYPE | None:
        """Indicaties the underline setting for this font.

        Value is |True|, |False|, |None|, or a member of the :ref:`MsoTextUnderlineType`
        enumeration. |None| is the default and indicates the underline setting should be inherited
        from the style hierarchy, such as from a placeholder. |True| indicates single underline.
        |False| indicates no underline. Other settings such as double and wavy underlining are
        indicated with members of the :ref:`MsoTextUnderlineType` enumeration.
        """
        u = self._rPr.u
        if u is MSO_UNDERLINE.NONE:
            return False
        if u is MSO_UNDERLINE.SINGLE_LINE:
            return True
        return u

    @underline.setter
    def underline(self, value: bool | MSO_TEXT_UNDERLINE_TYPE | None):
        if value is True:
            value = MSO_UNDERLINE.SINGLE_LINE
        elif value is False:
            value = MSO_UNDERLINE.NONE
        self._element.u = value

    def get_attrs(self) -> dict:
        """Return a dictionary of font attributes.

        Returns:
            dict: Font attributes including bold, color, italic, name, size (in points),
                  and underline.
        """
        return {
            "bold": self.bold,
            "strikethrough": self.strikethrough,
            "color": self.color,
            "italic": self.italic,
            "name": self.name,
            "size": self.size.pt if self.size is not None else None,
            "underline": self.underline,
        }

    def __hash__(self):
        return hash(tuple(self.get_attrs().values))

    def __eq__(self, other):
        if not isinstance(other, Font):
            return False
        return self.__hash__() == other.__hash__()

    def __repr__(self):
        return f"Font: name={self.name}, size={self.size}"

    def _to_dict_identity(
        self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private
    ):
        """Provide minimal identity information for Font objects."""
        identity = super()._to_dict_identity(
            _visited_ids, max_depth, expand_collections, format_for_llm, include_private
        )
        identity["description"] = "Font settings for text formatting"
        return identity

    def _to_dict_properties(
        self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
    ):
        """Extract all font properties for introspection."""
        props = {}

        # Core font properties - handle each individually for better error isolation
        font_attr_names = [
            "name",
            "size",
            "bold",
            "italic",
            "underline",
            "strikethrough",
            "language_id",
        ]

        for attr_name in font_attr_names:
            try:
                attr_value = getattr(self, attr_name)
                props[attr_name] = self._format_property_value_for_to_dict(
                    attr_value,
                    include_private,
                    _visited_ids,
                    max_depth,
                    expand_collections,
                    format_for_llm,
                )
            except Exception as e:
                props[attr_name] = self._create_error_context(
                    attr_name, e, "property access failed"
                )

        # Color requires special handling - use fill.to_dict() instead of self.color
        # since self.color is just self.fill.value and may be None
        try:
            if max_depth > 1:
                props["color"] = self.fill.to_dict(
                    include_relationships=False,
                    max_depth=max_depth - 1,
                    include_private=include_private,
                    expand_collections=expand_collections,
                    format_for_llm=format_for_llm,
                    _visited_ids=_visited_ids,
                )
            else:
                props["color"] = {"_object_type": "FillFormat", "_depth_exceeded": True}
        except Exception as e:
            props["color"] = self._create_error_context("color", e, "color format access failed")

        return props

    def _to_dict_relationships(
        self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
    ):
        """Font objects have no relationships to other objects."""
        return {}

    def _to_dict_llm_context(
        self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
    ):
        """Generate AI-friendly summary of font characteristics."""
        try:
            summary_parts = []

            # Extract font name
            if self.name:
                summary_parts.append(self.name)

            # Extract font size
            if self.size is not None:
                summary_parts.append(f"{self.size.pt}pt")

            # Extract style attributes
            styles = []
            if self.bold:
                styles.append("bold")
            if self.italic:
                styles.append("italic")

            # Extract underline info
            if self.underline is not None and self.underline is not False:
                if self.underline is True:
                    styles.append("underlined")
                else:
                    # Handle MSO_TEXT_UNDERLINE_TYPE enum
                    underline_name = getattr(self.underline, "name", str(self.underline))
                    styles.append(f"{underline_name.lower().replace('_', ' ')} underline")

            if self.strikethrough:
                styles.append("strikethrough")

            if styles:
                summary_parts.extend(styles)

            # Extract color information from fill
            try:
                color_summary = self._extract_color_summary()
                if color_summary:
                    summary_parts.append(f"color {color_summary}")
            except Exception:
                pass  # Ignore color extraction errors in summary

            # Build final summary
            if summary_parts:
                summary = " ".join(summary_parts) + "."
            else:
                summary = "Font settings are inherited."

            return {
                "summary": summary,
                "description": "Font object for text character formatting",
                "common_operations": [
                    "set font name",
                    "change font size",
                    "apply bold/italic",
                    "set color",
                    "configure underline",
                ],
            }
        except Exception as e:
            return {
                "summary": "Font object with undetermined properties.",
                "description": "Font introspection encountered an error",
                "error": str(e),
            }

    def _extract_color_summary(self):
        """Extract color summary from fill format for LLM context."""
        try:
            # Get color information through fill format
            fill_dict = self.fill.to_dict(
                include_relationships=False, max_depth=2, format_for_llm=True
            )

            if "_llm_context" in fill_dict and "summary" in fill_dict["_llm_context"]:
                color_summary = fill_dict["_llm_context"]["summary"]

                # Filter out non-useful color information
                if (
                    color_summary.startswith("No fill")
                    or color_summary.startswith("Background")
                    or "inherit" in color_summary.lower()
                    or color_summary.startswith("Gradient fill")
                    or color_summary.startswith("Pattern fill")
                    or color_summary == "Solid fill with color."
                ):
                    return None  # No useful color information for font context

                # Clean up the summary (remove "Solid" prefix if present)
                if color_summary.startswith("Solid "):
                    color_summary = color_summary[6:]

                return color_summary

            return None
        except Exception:
            return None


class _Hyperlink(Subshape):
    """Text run hyperlink object.

    Corresponds to `a:hlinkClick` child element of the run's properties element (`a:rPr`).
    """

    def __init__(self, rPr: CT_TextCharacterProperties, parent: ProvidesPart):
        super(_Hyperlink, self).__init__(parent)
        self._rPr = rPr

    @property
    def address(self) -> str | None:
        """The URL of the hyperlink.

        Read/write. URL can be on http, https, mailto, or file scheme; others may work.
        """
        if self._hlinkClick is None:
            return None
        return self.part.target_ref(self._hlinkClick.rId)

    @address.setter
    def address(self, url: str | None):
        # implements all three of add, change, and remove hyperlink
        if self._hlinkClick is not None:
            self._remove_hlinkClick()
        if url:
            self._add_hlinkClick(url)

    def _add_hlinkClick(self, url: str):
        rId = self.part.relate_to(url, RT.HYPERLINK, is_external=True)
        self._rPr.add_hlinkClick(rId)

    @property
    def _hlinkClick(self) -> CT_Hyperlink | None:
        return self._rPr.hlinkClick

    def _remove_hlinkClick(self):
        assert self._hlinkClick is not None
        self.part.drop_rel(self._hlinkClick.rId)
        self._rPr._remove_hlinkClick()  # pyright: ignore[reportPrivateUsage]


class _Paragraph(Subshape, IntrospectionMixin):
    """Paragraph object. Not intended to be constructed directly."""

    def __init__(self, p: CT_TextParagraph, parent: ProvidesPart):
        super(_Paragraph, self).__init__(parent)
        IntrospectionMixin.__init__(self)
        self._element = self._p = p

    def add_line_break(self):
        """Add line break at end of this paragraph."""
        self._p.add_br()

    def add_run(self) -> _Run:
        """Return a new run appended to the runs in this paragraph."""
        r = self._p.add_r()
        return _Run(r, self)

    @property
    def alignment(self) -> PP_PARAGRAPH_ALIGNMENT | None:
        """Horizontal alignment of this paragraph.

        The value |None| indicates the paragraph should 'inherit' its effective value from its
        style hierarchy. Assigning |None| removes any explicit setting, causing its inherited
        value to be used.
        """
        return self._pPr.algn

    @alignment.setter
    def alignment(self, value: PP_PARAGRAPH_ALIGNMENT | None):
        self._pPr.algn = value

    def clear(self):
        """Remove all content from this paragraph.

        Paragraph properties are preserved. Content includes runs, line breaks, and fields.
        """
        for elm in self._element.content_children:
            self._element.remove(elm)
        return self

    @property
    def font(self) -> Font:
        """|Font| object containing default character properties for the runs in this paragraph.

        These character properties override default properties inherited from parent objects such
        as the text frame the paragraph is contained in and they may be overridden by character
        properties set at the run level.
        """
        return Font(self._defRPr)

    @property
    def level(self) -> int:
        """Indentation level of this paragraph.

        Read-write. Integer in range 0..8 inclusive. 0 represents a top-level paragraph and is the
        default value. Indentation level is most commonly encountered in a bulleted list, as is
        found on a word bullet slide.
        """
        return self._pPr.lvl

    @level.setter
    def level(self, level: int):
        self._pPr.lvl = level

    @property
    def line_spacing(self) -> int | float | Length | None:
        """The space between baselines in successive lines of this paragraph.

        A value of |None| indicates no explicit value is assigned and its effective value is
        inherited from the paragraph's style hierarchy. A numeric value, e.g. `2` or `1.5`,
        indicates spacing is applied in multiples of line heights. A |Length| value such as
        `Pt(12)` indicates spacing is a fixed height. The |Pt| value class is a convenient way to
        apply line spacing in units of points.
        """
        pPr = self._p.pPr
        if pPr is None:
            return None
        return pPr.line_spacing

    @line_spacing.setter
    def line_spacing(self, value: int | float | Length | None):
        pPr = self._p.get_or_add_pPr()
        pPr.line_spacing = value

    @property
    def runs(self) -> tuple[_Run, ...]:
        """Sequence of runs in this paragraph."""
        return tuple(_Run(r, self) for r in self._element.r_lst)

    @property
    def space_after(self) -> Length | None:
        """The spacing to appear between this paragraph and the subsequent paragraph.

        A value of |None| indicates no explicit value is assigned and its effective value is
        inherited from the paragraph's style hierarchy. |Length| objects provide convenience
        properties, such as `.pt` and `.inches`, that allow easy conversion to various length
        units.
        """
        pPr = self._p.pPr
        if pPr is None:
            return None
        return pPr.space_after

    @space_after.setter
    def space_after(self, value: Length | None):
        pPr = self._p.get_or_add_pPr()
        pPr.space_after = value

    @property
    def space_before(self) -> Length | None:
        """The spacing to appear between this paragraph and the prior paragraph.

        A value of |None| indicates no explicit value is assigned and its effective value is
        inherited from the paragraph's style hierarchy. |Length| objects provide convenience
        properties, such as `.pt` and `.cm`, that allow easy conversion to various length units.
        """
        pPr = self._p.pPr
        if pPr is None:
            return None
        return pPr.space_before

    @space_before.setter
    def space_before(self, value: Length | None):
        pPr = self._p.get_or_add_pPr()
        pPr.space_before = value

    @property
    def text(self) -> str:
        """Text of paragraph as a single string.

        Read/write. This value is formed by concatenating the text in each run and field making up
        the paragraph, adding a vertical-tab character (`"\\v"`) for each line-break element
        (`<a:br>`, soft carriage-return) encountered.

        While the encoding of line-breaks as a vertical tab might be surprising at first, doing so
        is consistent with PowerPoint's clipboard copy behavior and allows a line-break to be
        distinguished from a paragraph boundary within the str return value.

        Assignment causes all content in the paragraph to be replaced. Each vertical-tab character
        (`"\\v"`) in the assigned str is translated to a line-break, as is each line-feed
        character (`"\\n"`). Contrast behavior of line-feed character in `TextFrame.text` setter.
        If line-feed characters are intended to produce new paragraphs, use `TextFrame.text`
        instead. Any other control characters in the assigned string are escaped as a hex
        representation like "_x001B_" (for ESC (ASCII 27) in this example).
        """
        return "".join(elm.text for elm in self._element.content_children)

    @text.setter
    def text(self, text: str):
        self.clear()
        self._element.append_text(text)

    @property
    def _defRPr(self) -> CT_TextCharacterProperties:
        """The element that defines the default run properties for runs in this paragraph.

        Causes the element to be added if not present.
        """
        return self._pPr.get_or_add_defRPr()

    @property
    def _pPr(self) -> CT_TextParagraphProperties:
        """Contains the properties for this paragraph.

        Causes the element to be added if not present.
        """
        return self._p.get_or_add_pPr()

    @property
    def bullet(self):
        pPr = self._p.pPr
        if pPr is None:
            return None
        return pPr.bullet

    @bullet.setter
    def bullet(self, value):
        pPr = self._p.get_or_add_pPr()
        if (
            pPr.find(
                "a:buFont",
                namespaces={"a": "http://schemas.openxmlformats.org/drawingml/2006/main"},
            )
            is None
        ):
            buFont = etree.Element(
                "{http://schemas.openxmlformats.org/drawingml/2006/main}buFont",
                typeface="Wingdings",
                pitchFamily="0",
                charset="2",
                panose="05000000000000000000",
            )
            pPr.insert(0, buFont)
        pPr.bullet = value

    def _to_dict_identity(
        self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private
    ):
        """Provide minimal identity information for _Paragraph objects."""
        identity = super()._to_dict_identity(
            _visited_ids, max_depth, expand_collections, format_for_llm, include_private
        )
        text_preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        text_preview = text_preview.replace("\n", " ").replace("\v", " ")
        identity["description"] = f'Paragraph containing: "{text_preview}"'
        return identity

    def _to_dict_properties(
        self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
    ):
        """Extract all paragraph properties for introspection."""
        props = {}

        # Core text content
        props["text"] = self.text

        # Paragraph formatting properties
        paragraph_attr_names = ["alignment", "level"]
        for attr_name in paragraph_attr_names:
            try:
                attr_value = getattr(self, attr_name)
                props[attr_name] = self._format_property_value_for_to_dict(
                    attr_value,
                    include_private,
                    _visited_ids,
                    max_depth,
                    expand_collections,
                    format_for_llm,
                )
            except Exception as e:
                props[attr_name] = self._create_error_context(
                    attr_name, e, "property access failed"
                )

        # Spacing properties - handle individually for better error isolation
        spacing_attr_names = ["line_spacing", "space_before", "space_after"]
        for attr_name in spacing_attr_names:
            try:
                attr_value = self._get_spacing_property_safely(attr_name)
                props[attr_name] = self._format_property_value_for_to_dict(
                    attr_value,
                    include_private,
                    _visited_ids,
                    max_depth,
                    expand_collections,
                    format_for_llm,
                )
            except Exception as e:
                props[attr_name] = self._create_error_context(
                    attr_name, e, "spacing property access failed"
                )

        # Bullet property
        try:
            bullet_value = self._get_bullet_property_safely()
            props["bullet"] = self._format_property_value_for_to_dict(
                bullet_value,
                include_private,
                _visited_ids,
                max_depth,
                expand_collections,
                format_for_llm,
            )
        except Exception as e:
            props["bullet"] = self._create_error_context(
                "bullet", e, "bullet property access failed"
            )

        # Default font (recursive call to FEP-007)
        try:
            if max_depth > 1:
                props["font"] = self.font.to_dict(
                    include_relationships=False,
                    max_depth=max_depth - 1,
                    include_private=include_private,
                    expand_collections=expand_collections,
                    format_for_llm=format_for_llm,
                    _visited_ids=_visited_ids,
                )
            else:
                props["font"] = {"_object_type": "Font", "_depth_exceeded": True}
        except Exception as e:
            props["font"] = self._create_error_context("font", e, "font access failed")

        # Runs collection (recursive calls to FEP-009)
        try:
            if expand_collections and max_depth > 1:
                runs_list = []
                for run in self.runs:
                    if hasattr(run, "to_dict"):
                        runs_list.append(
                            run.to_dict(
                                include_relationships=False,
                                max_depth=max_depth - 1,
                                include_private=include_private,
                                expand_collections=expand_collections,
                                format_for_llm=format_for_llm,
                                _visited_ids=_visited_ids,
                            )
                        )
                    else:
                        runs_list.append({"_object_type": "_Run", "_no_introspection": True})
                props["runs"] = runs_list
            elif expand_collections:
                props["runs"] = [
                    {"_object_type": "_Run", "_depth_exceeded": True} for _ in self.runs
                ]
            else:
                props["runs"] = {"_collection_summary": f"{len(self.runs)} runs"}
        except Exception as e:
            props["runs"] = self._create_error_context("runs", e, "runs collection access failed")

        return props

    def _to_dict_relationships(
        self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
    ):
        """Extract relationship information for paragraphs."""
        rels = {}

        # Parent relationship (text frame)
        try:
            if hasattr(self, "_parent") and self._parent is not None:
                rels["parent"] = {
                    "_object_type": "TextFrame",
                    "_description": "Parent text frame containing this paragraph",
                }
        except Exception:
            # Silently ignore parent relationship extraction errors
            pass

        # Child relationships (runs) - summary only to avoid deep nesting
        try:
            if len(self.runs) > 0:
                rels["runs"] = {
                    "_collection_summary": f"{len(self.runs)} child runs",
                    "_description": "Text runs contained in this paragraph",
                }
        except Exception:
            # Silently ignore runs relationship extraction errors
            pass

        return rels

    def _to_dict_llm_context(
        self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
    ):
        """Generate AI-friendly summary of paragraph characteristics."""
        try:
            # Extract text preview
            text_preview = self.text[:100].replace("\n", " ").replace("\v", " ")
            if len(self.text) > 100:
                text_preview += "..."

            # Build summary parts
            summary_parts = []

            # Add text content description
            if text_preview.strip():
                summary_parts.append(f'Paragraph: "{text_preview}"')
            else:
                summary_parts.append("Empty paragraph")

            # Add formatting information
            formatting_info = []

            # Alignment
            try:
                if self.alignment is not None:
                    alignment_name = getattr(self.alignment, "name", str(self.alignment))
                    formatting_info.append(f"{alignment_name.lower().replace('_', ' ')} aligned")
            except Exception:
                pass

            # Indentation level
            try:
                if self.level > 0:
                    formatting_info.append(f"indent level {self.level}")
            except Exception:
                pass

            # Spacing
            try:
                spacing_info = []
                if self.line_spacing is not None:
                    if isinstance(self.line_spacing, (int, float)):
                        spacing_info.append(f"{self.line_spacing}x line spacing")
                    else:
                        spacing_info.append("custom line spacing")

                if self.space_before is not None:
                    spacing_info.append("space before")

                if self.space_after is not None:
                    spacing_info.append("space after")

                if spacing_info:
                    formatting_info.extend(spacing_info)
            except Exception:
                pass

            # Bullet
            try:
                if self.bullet is not None:
                    formatting_info.append("bulleted")
            except Exception:
                pass

            if formatting_info:
                summary_parts.append("with " + ", ".join(formatting_info))

            # Runs information
            try:
                runs_count = len(self.runs)
                if runs_count == 1:
                    summary_parts.append("(1 text run)")
                elif runs_count > 1:
                    summary_parts.append(f"({runs_count} text runs)")
            except Exception:
                pass

            summary = " ".join(summary_parts) + "."

            return {
                "summary": summary,
                "description": "Paragraph object containing formatted text content",
                "common_operations": [
                    "modify text content (paragraph.text = ...)",
                    "change alignment (paragraph.alignment = ...)",
                    "set indentation (paragraph.level = ...)",
                    "adjust spacing (paragraph.line_spacing, space_before, space_after)",
                    "add/modify runs (paragraph.add_run())",
                    "format font (paragraph.font.bold = True, etc.)",
                ],
            }
        except Exception as e:
            return {
                "summary": f"Paragraph with {len(self.text)} characters.",
                "description": "Paragraph introspection encountered an error",
                "error": str(e),
            }

    def _get_spacing_property_safely(self, property_name):
        """Safely access spacing properties that may not be available."""
        try:
            return getattr(self, property_name)
        except (NotImplementedError, ValueError, AttributeError):
            return None

    def _get_bullet_property_safely(self):
        """Safely access bullet property that may not be available."""
        try:
            return self.bullet
        except (NotImplementedError, ValueError, AttributeError):
            return None


class _Run(Subshape, IntrospectionMixin):
    """Text run object. Corresponds to `a:r` child element in a paragraph."""

    def __init__(self, r: CT_RegularTextRun, parent: ProvidesPart):
        super(_Run, self).__init__(parent)
        IntrospectionMixin.__init__(self)
        self._r = r

    @property
    def font(self):
        """|Font| instance containing run-level character properties for the text in this run.

        Character properties can be and perhaps most often are inherited from parent objects such
        as the paragraph and slide layout the run is contained in. Only those specifically
        overridden at the run level are contained in the font object.
        """
        rPr = self._r.get_or_add_rPr()
        return Font(rPr)

    @lazyproperty
    def hyperlink(self) -> _Hyperlink:
        """Proxy for any `a:hlinkClick` element under the run properties element.

        Created on demand, the hyperlink object is available whether an `a:hlinkClick` element is
        present or not, and creates or deletes that element as appropriate in response to actions
        on its methods and attributes.
        """
        rPr = self._r.get_or_add_rPr()
        return _Hyperlink(rPr, self)

    @property
    def text(self):
        """Read/write. A unicode string containing the text in this run.

        Assignment replaces all text in the run. The assigned value can be a 7-bit ASCII
        string, a UTF-8 encoded 8-bit string, or unicode. String values are converted to
        unicode assuming UTF-8 encoding.

        Any other control characters in the assigned string other than tab or newline
        are escaped as a hex representation. For example, ESC (ASCII 27) is escaped as
        "_x001B_". Contrast the behavior of `TextFrame.text` and `_Paragraph.text` with
        respect to line-feed and vertical-tab characters.
        """
        return self._r.text

    @text.setter
    def text(self, text: str):
        self._r.text = text

    def _to_dict_identity(
        self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private
    ):
        """Provide minimal identity information for _Run objects."""
        identity = super()._to_dict_identity(
            _visited_ids, max_depth, expand_collections, format_for_llm, include_private
        )
        text_preview = self.text[:30] + "..." if len(self.text) > 30 else self.text
        identity["description"] = f'A text run containing: "{text_preview}"'
        return identity

    def _to_dict_properties(
        self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
    ):
        """Extract all run properties for introspection."""
        props = {}

        # Text content
        props["text"] = self.text

        # Font (recursive call to FEP-007)
        try:
            if max_depth > 1:
                props["font"] = self.font.to_dict(
                    include_relationships=False,
                    max_depth=max_depth - 1,
                    include_private=include_private,
                    expand_collections=expand_collections,
                    format_for_llm=format_for_llm,
                    _visited_ids=_visited_ids,
                )
            else:
                props["font"] = {"_object_type": "Font", "_depth_exceeded": True}
        except Exception as e:
            props["font"] = self._create_error_context("font", e, "font access failed")

        # Hyperlink address
        try:
            hlink = self.hyperlink
            props["hyperlink_address"] = hlink.address
        except Exception as e:
            props["hyperlink_address"] = self._create_error_context(
                "hyperlink_address", e, "hyperlink access failed"
            )

        return props

    def _to_dict_relationships(
        self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
    ):
        """Extract relationship information for hyperlinks."""
        rels = {}
        try:
            hlink = self.hyperlink
            if hlink.address is not None:
                # Get hyperlink rId from XML element
                hlink_click_elm = self._r.rPr.hlinkClick if self._r.rPr is not None else None
                if (
                    hlink_click_elm is not None
                    and hasattr(hlink_click_elm, "rId")
                    and hlink_click_elm.rId
                ):
                    rels["hyperlink"] = {
                        "rId": hlink_click_elm.rId,
                        "target_url": hlink.address,
                        "is_external": True,  # Hyperlinks from runs are usually external
                    }
        except Exception:
            # Silently ignore hyperlink relationship extraction errors
            pass
        return rels

    def _to_dict_llm_context(
        self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
    ):
        """Generate AI-friendly summary of run characteristics."""
        try:
            text_preview = self.text[:50].replace("\n", " ").replace("\v", " ")
            if len(self.text) > 50:
                text_preview += "..."

            font_summary = "default font"
            try:
                if max_depth > 0 and hasattr(self.font, "to_dict"):
                    font_dict = self.font.to_dict(
                        max_depth=0,
                        format_for_llm=True,
                        _visited_ids=_visited_ids,
                        include_relationships=False,
                        include_private=include_private,
                        expand_collections=expand_collections,
                    )
                    if "_llm_context" in font_dict and "summary" in font_dict["_llm_context"]:
                        font_summary = font_dict["_llm_context"]["summary"]
                        if "Font settings are inherited." in font_summary:
                            font_summary = "inherited font settings"
            except Exception:
                pass  # Use default font summary

            description_parts = [f'Text run: "{text_preview}"']
            description_parts.append(f"with {font_summary}")

            # Check for hyperlink
            try:
                hlink = self.hyperlink
                if hlink.address:
                    description_parts.append(f"hyperlinked to '{hlink.address}'")
            except Exception:
                pass  # Ignore hyperlink errors

            context = {}
            context["description"] = " ".join(p.rstrip(".") for p in description_parts) + "."
            # For runs, description is often a good summary
            context["summary"] = context["description"]

            context["common_operations"] = [
                "change text content (run.text = ...)",
                "modify font (run.font.bold = True, etc.)",
                "add/remove hyperlink (run.hyperlink.address = ...)",
            ]
            return context

        except Exception as e:
            return {
                "summary": f"Text run with {len(self.text)} characters.",
                "description": "Text run introspection encountered an error",
                "error": str(e),
            }
