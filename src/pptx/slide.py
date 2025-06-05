"""Slide-related objects, including masters, layouts, and notes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterator, cast

from pptx.dml.fill import FillFormat
from pptx.enum.shapes import PP_PLACEHOLDER
from pptx.introspection import IntrospectionMixin
from pptx.shapes.shapetree import (
    LayoutPlaceholders,
    LayoutShapes,
    MasterPlaceholders,
    MasterShapes,
    NotesSlidePlaceholders,
    NotesSlideShapes,
    SlidePlaceholders,
    SlideShapes,
)
from pptx.shared import ElementProxy, ParentedElementProxy, PartElementProxy
from pptx.util import lazyproperty

if TYPE_CHECKING:
    from pptx.oxml.presentation import CT_SlideIdList, CT_SlideMasterIdList
    from pptx.oxml.slide import (
        CT_CommonSlideData,
        CT_NotesSlide,
        CT_Slide,
        CT_SlideLayoutIdList,
        CT_SlideMaster,
    )
    from pptx.parts.presentation import PresentationPart
    from pptx.parts.slide import SlideLayoutPart, SlideMasterPart, SlidePart
    from pptx.presentation import Presentation
    from pptx.shapes.placeholder import LayoutPlaceholder, MasterPlaceholder
    from pptx.shapes.shapetree import NotesSlidePlaceholder
    from pptx.text.text import TextFrame


class _BaseSlide(PartElementProxy):
    """Base class for slide objects, including masters, layouts and notes."""

    _element: CT_Slide

    @lazyproperty
    def background(self) -> _Background:
        """|_Background| object providing slide background properties.

        This property returns a |_Background| object whether or not the
        slide, master, or layout has an explicitly defined background.

        The same |_Background| object is returned on every call for the same
        slide object.
        """
        return _Background(self._element.cSld)

    @property
    def name(self) -> str:
        """String representing the internal name of this slide.

        Returns an empty string (`''`) if no name is assigned. Assigning an empty string or |None|
        to this property causes any name to be removed.
        """
        return self._element.cSld.name

    @name.setter
    def name(self, value: str | None):
        new_value = "" if value is None else value
        self._element.cSld.name = new_value


class _BaseMaster(_BaseSlide):
    """Base class for master objects such as |SlideMaster| and |NotesMaster|.

    Provides access to placeholders and regular shapes.
    """

    @lazyproperty
    def placeholders(self) -> MasterPlaceholders:
        """|MasterPlaceholders| collection of placeholder shapes in this master.

        Sequence sorted in `idx` order.
        """
        return MasterPlaceholders(self._element.spTree, self)

    @lazyproperty
    def shapes(self):
        """
        Instance of |MasterShapes| containing sequence of shape objects
        appearing on this slide.
        """
        return MasterShapes(self._element.spTree, self)


class NotesMaster(_BaseMaster):
    """Proxy for the notes master XML document.

    Provides access to shapes, the most commonly used of which are placeholders.
    """


class NotesSlide(_BaseSlide):
    """Notes slide object.

    Provides access to slide notes placeholder and other shapes on the notes handout
    page.
    """

    element: CT_NotesSlide  # pyright: ignore[reportIncompatibleMethodOverride]

    def clone_master_placeholders(self, notes_master: NotesMaster) -> None:
        """Selectively add placeholder shape elements from `notes_master`.

        Selected placeholder shape elements from `notes_master` are added to the shapes
        collection of this notes slide. Z-order of placeholders is preserved. Certain
        placeholders (header, date, footer) are not cloned.
        """

        def iter_cloneable_placeholders() -> Iterator[MasterPlaceholder]:
            """Generate a reference to each cloneable placeholder in `notes_master`.

            These are the placeholders that should be cloned to a notes slide when the a new notes
            slide is created.
            """
            cloneable = (
                PP_PLACEHOLDER.SLIDE_IMAGE,
                PP_PLACEHOLDER.BODY,
                PP_PLACEHOLDER.SLIDE_NUMBER,
            )
            for placeholder in notes_master.placeholders:
                if placeholder.element.ph_type in cloneable:
                    yield placeholder

        shapes = self.shapes
        for placeholder in iter_cloneable_placeholders():
            shapes.clone_placeholder(cast("LayoutPlaceholder", placeholder))

    @property
    def notes_placeholder(self) -> NotesSlidePlaceholder | None:
        """the notes placeholder on this notes slide, the shape that contains the actual notes text.

        Return |None| if no notes placeholder is present; while this is probably uncommon, it can
        happen if the notes master does not have a body placeholder, or if the notes placeholder
        has been deleted from the notes slide.
        """
        for placeholder in self.placeholders:
            if placeholder.placeholder_format.type == PP_PLACEHOLDER.BODY:
                return placeholder
        return None

    @property
    def notes_text_frame(self) -> TextFrame | None:
        """The text frame of the notes placeholder on this notes slide.

        |None| if there is no notes placeholder. This is a shortcut to accommodate the common case
        of simply adding "notes" text to the notes "page".
        """
        notes_placeholder = self.notes_placeholder
        if notes_placeholder is None:
            return None
        return notes_placeholder.text_frame

    @lazyproperty
    def placeholders(self) -> NotesSlidePlaceholders:
        """Instance of |NotesSlidePlaceholders| for this notes-slide.

        Contains the sequence of placeholder shapes in this notes slide.
        """
        return NotesSlidePlaceholders(self.element.spTree, self)

    @lazyproperty
    def shapes(self) -> NotesSlideShapes:
        """Sequence of shape objects appearing on this notes slide."""
        return NotesSlideShapes(self._element.spTree, self)


class Slide(_BaseSlide, IntrospectionMixin):
    """Slide object. Provides access to shapes and slide-level properties."""

    part: SlidePart  # pyright: ignore[reportIncompatibleMethodOverride]

    def __init__(self, element, part):
        super(Slide, self).__init__(element, part)
        IntrospectionMixin.__init__(self)

    @property
    def follow_master_background(self):
        """|True| if this slide inherits the slide master background.

        Assigning |False| causes background inheritance from the master to be
        interrupted; if there is no custom background for this slide,
        a default background is added. If a custom background already exists
        for this slide, assigning |False| has no effect.

        Assigning |True| causes any custom background for this slide to be
        deleted and inheritance from the master restored.
        """
        return self._element.bg is None

    @property
    def has_notes_slide(self) -> bool:
        """`True` if this slide has a notes slide, `False` otherwise.

        A notes slide is created by :attr:`.notes_slide` when one doesn't exist; use this property
        to test for a notes slide without the possible side effect of creating one.
        """
        return self.part.has_notes_slide

    @property
    def notes_slide(self) -> NotesSlide:
        """The |NotesSlide| instance for this slide.

        If the slide does not have a notes slide, one is created. The same single instance is
        returned on each call.
        """
        return self.part.notes_slide

    @lazyproperty
    def placeholders(self) -> SlidePlaceholders:
        """Sequence of placeholder shapes in this slide."""
        return SlidePlaceholders(self._element.spTree, self)

    @lazyproperty
    def shapes(self) -> SlideShapes:
        """Sequence of shape objects appearing on this slide."""
        return SlideShapes(self._element.spTree, self)

    @property
    def slide_id(self) -> int:
        """Integer value that uniquely identifies this slide within this presentation.

        The slide id does not change if the position of this slide in the slide sequence is changed
        by adding, rearranging, or deleting slides.
        """
        return self.part.slide_id

    @property
    def slide_layout(self) -> SlideLayout:
        """|SlideLayout| object this slide inherits appearance from."""
        return self.part.slide_layout

    # -- IntrospectionMixin overrides --

    def _to_dict_identity(
        self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private
    ):
        """Override to provide slide-specific identity information."""
        identity = super()._to_dict_identity(
            _visited_ids, max_depth, expand_collections, format_for_llm, include_private
        )
        identity["description"] = f"Represents slide ID {self.slide_id}."
        identity["slide_id"] = self.slide_id
        if self.name:  # slide.name can be empty string
            identity["name"] = self.name
        return identity

    def _to_dict_properties(
        self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
    ):
        """Override to expose slide properties and collections."""
        props = {}

        # Basic slide properties
        props["has_notes_slide"] = self.has_notes_slide
        props["follow_master_background"] = self.follow_master_background

        # Shapes collection (recursive, FEP-003/008 etc.)
        try:
            if expand_collections and max_depth > 0:
                shapes_list = []
                for shape in self.shapes:
                    if hasattr(shape, "to_dict"):
                        shapes_list.append(
                            shape.to_dict(
                                include_relationships=True,
                                max_depth=max_depth - 1,
                                include_private=include_private,
                                expand_collections=expand_collections,
                                format_for_llm=format_for_llm,
                                _visited_ids=_visited_ids,
                            )
                        )
                    else:
                        shapes_list.append({"_object_type": "BaseShape", "_no_introspection": True})
                props["shapes"] = shapes_list
            elif expand_collections:
                props["shapes"] = [
                    {"_object_type": "BaseShape", "_depth_exceeded": True} for _ in self.shapes
                ]
            else:
                props["shapes"] = {"_collection_summary": f"{len(self.shapes)} shapes"}
        except Exception as e:
            props["shapes"] = self._create_error_context(
                "shapes", e, "shapes collection access failed"
            )

        # Placeholders collection
        try:
            if expand_collections and max_depth > 0:
                placeholders_list = []
                for ph_idx, placeholder in self.placeholders.items():
                    if hasattr(placeholder, "to_dict"):
                        placeholders_list.append(
                            {
                                "placeholder_idx": ph_idx,
                                "placeholder_data": placeholder.to_dict(
                                    include_relationships=True,
                                    max_depth=max_depth - 1,
                                    include_private=include_private,
                                    expand_collections=expand_collections,
                                    format_for_llm=format_for_llm,
                                    _visited_ids=_visited_ids,
                                ),
                            }
                        )
                    else:
                        placeholders_list.append(
                            {
                                "placeholder_idx": ph_idx,
                                "placeholder_data": {
                                    "_object_type": "Placeholder",
                                    "_no_introspection": True,
                                },
                            }
                        )
                props["placeholders"] = placeholders_list
            elif expand_collections:
                props["placeholders"] = [
                    {"placeholder_idx": ph_idx, "_depth_exceeded": True}
                    for ph_idx in self.placeholders
                ]
            else:
                props["placeholders"] = {
                    "_collection_summary": f"{len(self.placeholders)} placeholders"
                }
        except Exception as e:
            props["placeholders"] = self._create_error_context(
                "placeholders", e, "placeholders collection access failed"
            )

        return props

    def _to_dict_relationships(
        self, remaining_depth, expand_collections, _visited_ids, format_for_llm, include_private
    ):
        """Override to include slide relationships."""
        rels = super()._to_dict_relationships(
            remaining_depth, expand_collections, _visited_ids, format_for_llm, include_private
        )

        # Slide Layout
        if self.slide_layout:
            if hasattr(self.slide_layout, "to_dict"):
                try:
                    rels["slide_layout"] = self.slide_layout.to_dict(
                        max_depth=0,  # Summary only
                        _visited_ids=_visited_ids,
                        include_relationships=False,
                        expand_collections=False,
                        format_for_llm=format_for_llm,
                        include_private=include_private,
                    )
                except Exception:
                    rels["slide_layout_ref"] = repr(self.slide_layout)
            else:
                rels["slide_layout_ref"] = repr(self.slide_layout)

        # Notes Slide
        if self.has_notes_slide:
            try:
                notes_slide = self.notes_slide
                if hasattr(notes_slide, "to_dict"):
                    rels["notes_slide"] = notes_slide.to_dict(
                        max_depth=remaining_depth - 1 if remaining_depth > 0 else 0,
                        _visited_ids=_visited_ids,
                        include_relationships=True,
                        expand_collections=expand_collections,
                        format_for_llm=format_for_llm,
                        include_private=include_private,
                    )
                else:
                    rels["notes_slide_ref"] = repr(notes_slide)
            except Exception as e:
                rels["notes_slide_error"] = f"Error accessing notes slide: {str(e)}"

        # Parent Presentation (via part.package.presentation_part.presentation)
        try:
            prs = self.part.package.presentation_part.presentation
            if hasattr(prs, "to_dict"):
                rels["parent_presentation"] = prs.to_dict(
                    max_depth=0,  # Summary only
                    _visited_ids=_visited_ids,
                    include_relationships=False,
                    expand_collections=False,
                    format_for_llm=format_for_llm,
                    include_private=include_private,
                )
            else:
                rels["parent_presentation_ref"] = repr(prs)
        except Exception:
            # Broad except for safety - parent presentation access can fail in various ways
            pass

        return rels

    def _to_dict_llm_context(
        self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private
    ):
        """Override to provide slide-specific LLM context."""
        context = super()._to_dict_llm_context(
            _visited_ids, max_depth, expand_collections, format_for_llm, include_private
        )

        # Build descriptive context
        try:
            # Get title text if available
            title_text = None
            title_preview = ""
            try:
                if self.shapes.title and self.shapes.title.has_text_frame:
                    title_text = self.shapes.title.text
                    if title_text:
                        title_preview = title_text[:50].replace("\n", " ").replace("\v", " ")
                        if len(title_text) > 50:
                            title_preview += "..."
                        title_preview = f' with title "{title_preview}"'
            except Exception:
                pass

            # Get layout name
            layout_name = "a standard layout"
            try:
                if self.slide_layout and self.slide_layout.name:
                    layout_name = f"layout '{self.slide_layout.name}'"
            except Exception:
                pass

            # Build description
            desc_parts = []
            slide_identifier = f"Slide ID {self.slide_id}"
            if self.name:
                slide_identifier += f" named '{self.name}'"
            desc_parts.append(f"{slide_identifier}{title_preview}, based on {layout_name}.")

            desc_parts.append(
                f"Contains {len(self.shapes)} shape(s) including "
                f"{len(self.placeholders)} placeholder(s)."
            )

            if self.has_notes_slide:
                desc_parts.append("Has speaker notes.")

            context["description"] = " ".join(desc_parts)
            context["summary"] = context["description"]

            context["common_operations"] = [
                "access shapes (slide.shapes)",
                "access placeholders (slide.placeholders, slide.shapes.title)",
                "add shapes (slide.shapes.add_shape(...), etc.)",
                "access slide layout (slide.slide_layout)",
                "access/modify notes (slide.notes_slide.notes_text_frame.text = ...)",
                "get slide properties (slide.slide_id, slide.name, slide.follow_master_background)",
            ]

        except Exception as e:
            context["description"] = f"Slide ID {self.slide_id} with introspection error: {str(e)}"
            context["summary"] = context["description"]

        return context


class Slides(ParentedElementProxy):
    """Sequence of slides belonging to an instance of |Presentation|.

    Has list semantics for access to individual slides. Supports indexed access, len(), and
    iteration.
    """

    part: PresentationPart  # pyright: ignore[reportIncompatibleMethodOverride]

    def __init__(self, sldIdLst: CT_SlideIdList, prs: Presentation):
        super(Slides, self).__init__(sldIdLst, prs)
        self._sldIdLst = sldIdLst

    def __getitem__(self, idx: int) -> Slide:
        """Provide indexed access, (e.g. 'slides[0]')."""
        try:
            sldId = self._sldIdLst.sldId_lst[idx]
        except IndexError:
            raise IndexError("slide index out of range")
        return self.part.related_slide(sldId.rId)

    def __iter__(self) -> Iterator[Slide]:
        """Support iteration, e.g. `for slide in slides:`."""
        for sldId in self._sldIdLst.sldId_lst:
            yield self.part.related_slide(sldId.rId)

    def __len__(self) -> int:
        """Support len() built-in function, e.g. `len(slides) == 4`."""
        return len(self._sldIdLst)

    def add_slide(self, slide_layout: SlideLayout) -> Slide:
        """Return a newly added slide that inherits layout from `slide_layout`."""
        rId, slide = self.part.add_slide(slide_layout)
        slide.shapes.clone_layout_placeholders(slide_layout)
        self._sldIdLst.add_sldId(rId)
        return slide

    def get(self, slide_id: int, default: Slide | None = None) -> Slide | None:
        """Return the slide identified by int `slide_id` in this presentation.

        Returns `default` if not found.
        """
        slide = self.part.get_slide(slide_id)
        if slide is None:
            return default
        return slide

    def index(self, slide: Slide) -> int:
        """Map `slide` to its zero-based position in this slide sequence.

        Raises |ValueError| on *slide* not present.
        """
        for idx, this_slide in enumerate(self):
            if this_slide == slide:
                return idx
        raise ValueError("%s is not in slide collection" % slide)


class SlideLayout(_BaseSlide, IntrospectionMixin):
    """Slide layout object.

    Provides access to placeholders, regular shapes, and slide layout-level properties.
    """

    part: SlideLayoutPart  # pyright: ignore[reportIncompatibleMethodOverride]

    def __init__(self, element, part):
        super(SlideLayout, self).__init__(element, part)
        IntrospectionMixin.__init__(self)

    def iter_cloneable_placeholders(self) -> Iterator[LayoutPlaceholder]:
        """Generate layout-placeholders on this slide-layout that should be cloned to a new slide.

        Used when creating a new slide from this slide-layout.
        """
        latent_ph_types = (
            PP_PLACEHOLDER.DATE,
            PP_PLACEHOLDER.FOOTER,
            PP_PLACEHOLDER.SLIDE_NUMBER,
        )
        for ph in self.placeholders:
            if ph.element.ph_type not in latent_ph_types:
                yield ph

    @lazyproperty
    def placeholders(self) -> LayoutPlaceholders:
        """Sequence of placeholder shapes in this slide layout.

        Placeholders appear in `idx` order.
        """
        return LayoutPlaceholders(self._element.spTree, self)

    @lazyproperty
    def shapes(self) -> LayoutShapes:
        """Sequence of shapes appearing on this slide layout."""
        return LayoutShapes(self._element.spTree, self)

    @property
    def slide_master(self) -> SlideMaster:
        """Slide master from which this slide-layout inherits properties."""
        return self.part.slide_master

    @property
    def used_by_slides(self):
        """Tuple of slide objects based on this slide layout."""
        # ---getting Slides collection requires going around the horn a bit---
        slides = self.part.package.presentation_part.presentation.slides
        return tuple(s for s in slides if s.slide_layout == self)

    # -- IntrospectionMixin overrides --

    def _to_dict_identity(
        self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private
    ):
        """Override to provide slide layout-specific identity information."""
        identity = super()._to_dict_identity(
            _visited_ids, max_depth, expand_collections, format_for_llm, include_private
        )
        layout_name = self.name if self.name else "Unnamed Layout"
        identity["description"] = f"Slide Layout: '{layout_name}'"
        if self.name:
            identity["name"] = self.name
        return identity

    def _to_dict_properties(
        self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
    ):
        """Override to expose slide layout properties and collections."""
        props = {}

        # Background fill (recursive, leverages FEP-005)
        if max_depth > 1:  # Need depth > 1 to recurse into FillFormat
            try:
                props["background_fill"] = self.background.fill.to_dict(
                    include_relationships=True,
                    max_depth=max_depth - 1,
                    include_private=include_private,
                    expand_collections=expand_collections,
                    format_for_llm=format_for_llm,
                    _visited_ids=_visited_ids,
                )
            except Exception as e:
                props["background_fill"] = self._create_error_context(
                    "background_fill", e, "background fill access failed"
                )
        else:
            props["background_fill"] = {"_object_type": "FillFormat", "_depth_exceeded": True}

        # Non-placeholder shapes collection
        try:
            non_placeholder_shapes = [s for s in self.shapes if not s.is_placeholder]
            if expand_collections and max_depth > 0:
                shapes_list = []
                for shape in non_placeholder_shapes:
                    if hasattr(shape, "to_dict"):
                        shapes_list.append(
                            shape.to_dict(
                                include_relationships=True,
                                max_depth=max_depth - 1,
                                include_private=include_private,
                                expand_collections=expand_collections,
                                format_for_llm=format_for_llm,
                                _visited_ids=_visited_ids,
                            )
                        )
                    else:
                        shapes_list.append({"_object_type": "BaseShape", "_no_introspection": True})
                props["non_placeholder_shapes"] = shapes_list
            elif expand_collections:
                props["non_placeholder_shapes"] = [
                    {"_object_type": "BaseShape", "_depth_exceeded": True}
                    for _ in non_placeholder_shapes
                ]
            else:
                props["non_placeholder_shapes"] = {
                    "_collection_summary": f"{len(non_placeholder_shapes)} non-placeholder shapes"
                }
        except Exception as e:
            props["non_placeholder_shapes"] = self._create_error_context(
                "non_placeholder_shapes", e, "non-placeholder shapes collection access failed"
            )

        # Placeholders collection (recursive, uses LayoutPlaceholder.to_dict())
        try:
            if expand_collections and max_depth > 0:
                placeholders_list = []
                for placeholder in self.placeholders:
                    placeholder_entry = {}
                    # Try to get placeholder index if available
                    try:
                        placeholder_entry["placeholder_idx"] = placeholder.placeholder_format.idx
                    except Exception:
                        placeholder_entry["placeholder_idx"] = None

                    if hasattr(placeholder, "to_dict"):
                        placeholder_entry["placeholder_data"] = placeholder.to_dict(
                            include_relationships=True,
                            max_depth=max_depth - 1,
                            include_private=include_private,
                            expand_collections=expand_collections,
                            format_for_llm=format_for_llm,
                            _visited_ids=_visited_ids,
                        )
                    else:
                        placeholder_entry["placeholder_data"] = {
                            "_object_type": "LayoutPlaceholder",
                            "_no_introspection": True,
                            "name": getattr(placeholder, "name", "Unnamed"),
                        }
                    placeholders_list.append(placeholder_entry)
                props["placeholders"] = placeholders_list
            elif expand_collections:
                props["placeholders"] = [
                    {"placeholder_idx": getattr(ph.placeholder_format, "idx", None), "_depth_exceeded": True}
                    for ph in self.placeholders
                ]
            else:
                props["placeholders"] = {
                    "_collection_summary": f"{len(self.placeholders)} placeholders"
                }
        except Exception as e:
            props["placeholders"] = self._create_error_context(
                "placeholders", e, "placeholders collection access failed"
            )

        return props

    def _to_dict_relationships(
        self, remaining_depth, expand_collections, _visited_ids, format_for_llm, include_private
    ):
        """Override to include slide layout relationships."""
        rels = {}

        # Slide Master
        try:
            if self.slide_master:
                if hasattr(self.slide_master, "to_dict"):
                    try:
                        rels["slide_master"] = self.slide_master.to_dict(
                            max_depth=0,  # Summary only
                            _visited_ids=_visited_ids,
                            include_relationships=False,
                            expand_collections=False,
                            format_for_llm=format_for_llm,
                            include_private=include_private,
                        )
                    except Exception:
                        rels["slide_master_ref"] = repr(self.slide_master)
                else:
                    rels["slide_master_ref"] = repr(self.slide_master)
        except Exception:
            pass

        # Used by Slides (this could be a large list, so limit expansion)
        try:
            used_by_slides = self.used_by_slides
            if remaining_depth > 0 and expand_collections and len(used_by_slides) <= 5:
                # Only expand if we have few slides and sufficient depth
                used_by_slides_data = []
                for slide in used_by_slides:
                    if hasattr(slide, "to_dict"):
                        try:
                            used_by_slides_data.append(
                                slide.to_dict(
                                    max_depth=0,  # Summary only to avoid circular references
                                    _visited_ids=_visited_ids,
                                    include_relationships=False,
                                    expand_collections=False,
                                    format_for_llm=format_for_llm,
                                    include_private=include_private,
                                )
                            )
                        except Exception:
                            used_by_slides_data.append({
                                "_object_type": "Slide",
                                "slide_id": getattr(slide, "slide_id", "unknown"),
                            })
                    else:
                        used_by_slides_data.append(
                            {"_object_type": "Slide", "_no_introspection": True}
                        )
                rels["used_by_slides"] = used_by_slides_data
            else:
                rels["used_by_slides_summary"] = f"Used by {len(used_by_slides)} slide(s)"
        except Exception as e:
            rels["used_by_slides_error"] = f"Error accessing used_by_slides: {str(e)}"

        return rels

    def _to_dict_llm_context(
        self, _visited_ids, max_depth, expand_collections, format_for_llm, include_private
    ):
        """Override to provide slide layout-specific LLM context."""
        context = {}

        try:
            # Build descriptive context
            layout_name = self.name if self.name else "Unnamed Layout"
            master_name = "Unknown Master"
            try:
                if self.slide_master and self.slide_master.name:
                    master_name = self.slide_master.name
                elif self.slide_master:
                    master_name = "a slide master"
            except Exception:
                pass

            desc_parts = []
            desc_parts.append(
                f"Slide Layout '{layout_name}', based on slide master '{master_name}'"
            )

            # Count shapes and placeholders
            try:
                total_shapes = len(self.shapes)
                total_placeholders = len(self.placeholders)
                desc_parts.append(
                    f"Contains {total_shapes} total shapes, of which "
                    f"{total_placeholders} are placeholders"
                )
            except Exception:
                desc_parts.append("Contains shapes and placeholders")

            # Usage information
            try:
                used_by_count = len(self.used_by_slides)
                if used_by_count == 0:
                    desc_parts.append("Not currently used by any slides")
                elif used_by_count == 1:
                    desc_parts.append("Used by 1 slide")
                else:
                    desc_parts.append(f"Used by {used_by_count} slides")
            except Exception:
                desc_parts.append("Usage by slides unknown")

            context["description"] = ". ".join(desc_parts) + "."
            context["summary"] = context["description"]

            context["common_operations"] = [
                "access shapes (slide_layout.shapes)",
                "access placeholders (slide_layout.placeholders)",
                "access parent slide master (slide_layout.slide_master)",
                "check which slides use this layout (slide_layout.used_by_slides)",
                "access background (slide_layout.background.fill)",
                "iterate cloneable placeholders (slide_layout.iter_cloneable_placeholders())",
            ]

        except Exception as e:
            context["description"] = f"Slide Layout with introspection error: {str(e)}"
            context["summary"] = context["description"]

        return context


class SlideLayouts(ParentedElementProxy):
    """Sequence of slide layouts belonging to a slide-master.

    Supports indexed access, len(), iteration, index() and remove().
    """

    part: SlideMasterPart  # pyright: ignore[reportIncompatibleMethodOverride]

    def __init__(self, sldLayoutIdLst: CT_SlideLayoutIdList, parent: SlideMaster):
        super(SlideLayouts, self).__init__(sldLayoutIdLst, parent)
        self._sldLayoutIdLst = sldLayoutIdLst

    def __getitem__(self, idx: int) -> SlideLayout:
        """Provides indexed access, e.g. `slide_layouts[2]`."""
        try:
            sldLayoutId = self._sldLayoutIdLst.sldLayoutId_lst[idx]
        except IndexError:
            raise IndexError("slide layout index out of range")
        return self.part.related_slide_layout(sldLayoutId.rId)

    def __iter__(self) -> Iterator[SlideLayout]:
        """Generate each |SlideLayout| in the collection, in sequence."""
        for sldLayoutId in self._sldLayoutIdLst.sldLayoutId_lst:
            yield self.part.related_slide_layout(sldLayoutId.rId)

    def __len__(self) -> int:
        """Support len() built-in function, e.g. `len(slides) == 4`."""
        return len(self._sldLayoutIdLst)

    def get_by_name(self, name: str, default: SlideLayout | None = None) -> SlideLayout | None:
        """Return SlideLayout object having `name`, or `default` if not found."""
        for slide_layout in self:
            if slide_layout.name == name:
                return slide_layout
        return default

    def index(self, slide_layout: SlideLayout) -> int:
        """Return zero-based index of `slide_layout` in this collection.

        Raises `ValueError` if `slide_layout` is not present in this collection.
        """
        for idx, this_layout in enumerate(self):
            if slide_layout == this_layout:
                return idx
        raise ValueError("layout not in this SlideLayouts collection")

    def remove(self, slide_layout: SlideLayout) -> None:
        """Remove `slide_layout` from the collection.

        Raises ValueError when `slide_layout` is in use; a slide layout which is the basis for one
        or more slides cannot be removed.
        """
        # ---raise if layout is in use---
        if slide_layout.used_by_slides:
            raise ValueError("cannot remove slide-layout in use by one or more slides")

        # ---target layout is identified by its index in this collection---
        target_idx = self.index(slide_layout)

        # --remove layout from p:sldLayoutIds of its master
        # --this stops layout from showing up, but doesn't remove it from package
        target_sldLayoutId = self._sldLayoutIdLst.sldLayoutId_lst[target_idx]
        self._sldLayoutIdLst.remove(target_sldLayoutId)

        # --drop relationship from master to layout
        # --this removes layout from package, along with everything (only) it refers to,
        # --including images (not used elsewhere) and hyperlinks
        slide_layout.slide_master.part.drop_rel(target_sldLayoutId.rId)


class SlideMaster(_BaseMaster, IntrospectionMixin):
    """Slide master object.

    Provides access to slide layouts. Access to placeholders, regular shapes, and slide master-level
    properties is inherited from |_BaseMaster|.
    """

    _element: CT_SlideMaster  # pyright: ignore[reportIncompatibleVariableOverride]

    def __init__(self, element, part):
        """Initialize SlideMaster with IntrospectionMixin support."""
        super(SlideMaster, self).__init__(element, part)
        IntrospectionMixin.__init__(self)

    @lazyproperty
    def slide_layouts(self) -> SlideLayouts:
        """|SlideLayouts| object providing access to this slide-master's layouts."""
        return SlideLayouts(self._element.get_or_add_sldLayoutIdLst(), self)

    def _to_dict_identity(
        self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
    ):
        """Override to include slide master-specific identity information."""
        identity = super()._to_dict_identity(
            include_private, _visited_ids, max_depth, expand_collections, format_for_llm
        )

        identity["description"] = f"Slide Master: '{self.name if self.name else 'Default Master'}'"
        if self.name:
            identity["name"] = self.name

        return identity

    def _to_dict_properties(
        self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
    ):
        """Override to include slide master-specific properties."""
        # Call parent method first to get base properties
        props = super()._to_dict_properties(
            include_private, _visited_ids, max_depth, expand_collections, format_for_llm
        )

        try:
            # Background Fill (recursive, uses FEP-005)
            try:
                if max_depth > 0:
                    props["background_fill"] = self.background.fill.to_dict(
                        include_private=include_private,
                        _visited_ids=_visited_ids,
                        max_depth=max_depth - 1,
                        expand_collections=expand_collections,
                        format_for_llm=format_for_llm,
                    )
                else:
                    props["background_fill"] = {
                        "_object_type": "FillFormat", 
                        "_depth_exceeded": True
                    }
            except Exception as e:
                props["background_fill"] = self._create_error_context(
                    "background_fill", e, "accessing background fill"
                )

            # Shapes (non-placeholders) & Placeholders
            try:
                all_shapes = list(self.shapes)
                non_placeholder_shapes = [s for s in all_shapes if not s.is_placeholder]

                if expand_collections and max_depth > 0:
                    props["shapes"] = []
                    for shape in non_placeholder_shapes:
                        try:
                            if hasattr(shape, 'to_dict'):
                                props["shapes"].append(shape.to_dict(
                                    include_private=include_private,
                                    _visited_ids=_visited_ids,
                                    max_depth=max_depth - 1,
                                    expand_collections=expand_collections,
                                    format_for_llm=format_for_llm,
                                ))
                            else:
                                props["shapes"].append({"_object_ref": repr(shape)})
                        except Exception as e:
                            props["shapes"].append(self._create_error_context(
                                "shape", e, f"accessing shape {getattr(shape, 'shape_id', 'unknown')}"
                            ))

                    # Master placeholders accessed by iteration (not keyed like layout placeholders)
                    props["placeholders"] = []
                    try:
                        for ph in self.placeholders:
                            ph_dict = {}
                            # Try to get the placeholder type from the placeholder itself
                            try:
                                if hasattr(ph, 'placeholder_format') and ph.placeholder_format:
                                    ph_type = ph.placeholder_format.type
                                    ph_dict["placeholder_type_key"] = self._format_property_value_for_to_dict(
                                        ph_type, include_private, _visited_ids, max_depth,
                                        expand_collections, format_for_llm
                                    )
                            except Exception:
                                ph_dict["placeholder_type_key"] = "Unknown"

                            try:
                                if hasattr(ph, 'to_dict'):
                                    ph_dict.update(ph.to_dict(
                                        include_private=include_private,
                                        _visited_ids=_visited_ids,
                                        max_depth=max_depth - 1,
                                        expand_collections=expand_collections,
                                        format_for_llm=format_for_llm,
                                    ))
                                else:
                                    ph_dict["_object_ref"] = repr(ph)
                            except Exception as e:
                                ph_dict.update(self._create_error_context(
                                    "placeholder", e, "accessing placeholder"
                                ))
                            props["placeholders"].append(ph_dict)
                    except Exception as e:
                        props["placeholders"] = self._create_error_context(
                            "placeholders", e, "accessing placeholders collection"
                        )
                else:
                    props["shapes"] = f"Collection of {len(non_placeholder_shapes)} non-placeholder shapes"
                    try:
                        placeholder_count = len(self.placeholders)
                        props["placeholders"] = f"Collection of {placeholder_count} placeholders"
                    except Exception:
                        props["placeholders"] = "Collection of placeholders (count unavailable)"

            except Exception as e:
                props["shapes"] = self._create_error_context("shapes", e, "accessing shapes collection")
                props["placeholders"] = self._create_error_context("placeholders", e, "accessing placeholders collection")

            # Color Map (<p:clrMap>)
            try:
                clrMap = self._element.clrMap
                if clrMap is not None:
                    props["color_map"] = {
                        "bg1": getattr(clrMap, 'bg1', None),
                        "tx1": getattr(clrMap, 'tx1', None),
                        "bg2": getattr(clrMap, 'bg2', None),
                        "tx2": getattr(clrMap, 'tx2', None),
                        "accent1": getattr(clrMap, 'accent1', None),
                        "accent2": getattr(clrMap, 'accent2', None),
                        "accent3": getattr(clrMap, 'accent3', None),
                        "accent4": getattr(clrMap, 'accent4', None),
                        "accent5": getattr(clrMap, 'accent5', None),
                        "accent6": getattr(clrMap, 'accent6', None),
                        "hlink": getattr(clrMap, 'hlink', None),
                        "folHlink": getattr(clrMap, 'folHlink', None),
                    }
                else:
                    props["color_map"] = None
            except Exception as e:
                props["color_map"] = self._create_error_context("color_map", e, "accessing color map")

            # Text Styles (<p:txStyles>) - Summary only
            try:
                txStyles = getattr(self._element, 'txStyles', None)
                props["text_styles_summary"] = {
                    "present": txStyles is not None,
                    "_note": "Full text style introspection is deferred to a future FEP."
                }
                if txStyles is not None:
                    # Add basic information about available style types
                    style_types = []
                    for style_type in ['titleStyle', 'bodyStyle', 'otherStyle']:
                        if hasattr(txStyles, style_type) and getattr(txStyles, style_type) is not None:
                            style_types.append(style_type)
                    props["text_styles_summary"]["available_styles"] = style_types
            except Exception as e:
                props["text_styles_summary"] = self._create_error_context("text_styles", e, "accessing text styles")

        except Exception as e:
            props["_slide_master_properties_error"] = f"Error accessing slide master properties: {str(e)}"

        return props

    def _to_dict_relationships(
        self, remaining_depth, expand_collections, _visited_ids, format_for_llm, include_private
    ):
        """Override to include slide master relationships."""
        rels = {}

        try:
            # Slide Layouts Collection
            try:
                slide_layouts = list(self.slide_layouts)

                if expand_collections and remaining_depth > 0:
                    rels["slide_layouts"] = []
                    for sl in slide_layouts:
                        try:
                            if hasattr(sl, 'to_dict'):
                                # Use at least depth 1 to get basic structure from SlideLayout
                                layout_depth = max(1, remaining_depth - 1)
                                rels["slide_layouts"].append(sl.to_dict(
                                    include_private=include_private,
                                    _visited_ids=_visited_ids,
                                    max_depth=layout_depth,
                                    expand_collections=expand_collections,
                                    format_for_llm=format_for_llm,
                                ))
                            else:
                                rels["slide_layouts"].append({"_object_ref": repr(sl)})
                        except Exception as e:
                            rels["slide_layouts"].append(self._create_error_context(
                                "slide_layout", e, f"accessing slide layout {getattr(sl, 'name', 'unknown')}"
                            ))
                else:
                    rels["slide_layouts_summary"] = f"Manages {len(slide_layouts)} slide layout(s)"

            except Exception as e:
                rels["slide_layouts"] = self._create_error_context("slide_layouts", e, "accessing slide layouts collection")

            # Theme Part (summary ref only)
            try:
                from pptx.opc.constants import RELATIONSHIP_TYPE as RT
                theme_part = self.part.part_related_by(RT.THEME)
                rels["theme_part_ref"] = {
                    "partname": str(theme_part.partname),
                    "_object_type": type(theme_part).__name__
                }
            except (KeyError, AttributeError):
                rels["theme_part_ref"] = "No theme part explicitly linked"
            except Exception as e:
                rels["theme_part_ref"] = self._create_error_context("theme_part", e, "accessing theme part")

            # Parent Presentation (summary ref only)
            try:
                if hasattr(self, 'part') and hasattr(self.part, 'presentation_part'):
                    pres_part = self.part.presentation_part
                    if hasattr(pres_part, 'presentation') and remaining_depth > 0:
                        presentation = pres_part.presentation
                        if hasattr(presentation, 'to_dict'):
                            rels["parent_presentation"] = presentation.to_dict(
                                max_depth=0,  # Summary only to avoid circular reference
                                include_relationships=False,
                                expand_collections=False,
                                format_for_llm=format_for_llm,
                                include_private=include_private,
                                _visited_ids=_visited_ids,
                            )
                        else:
                            rels["parent_presentation_ref"] = repr(presentation)
                    else:
                        rels["parent_presentation_ref"] = "Presentation reference unavailable"
                else:
                    rels["parent_presentation"] = None
            except Exception as e:
                rels["parent_presentation"] = self._create_error_context("parent_presentation", e, "accessing parent presentation")

        except Exception as e:
            rels["_slide_master_relationships_error"] = f"Error accessing slide master relationships: {str(e)}"

        return rels

    def _to_dict_llm_context(
        self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
    ):
        """Override to provide slide master-specific LLM context."""
        context = {}

        try:
            # Build description
            master_name = self.name if self.name else "Default Master"

            # Get layout count
            layout_count = 0
            try:
                layout_count = len(self.slide_layouts)
            except Exception:
                pass

            # Get placeholder count
            placeholder_count = 0
            try:
                placeholder_count = len(self.placeholders)
            except Exception:
                pass

            # Get shape count
            shape_count = 0
            try:
                all_shapes = list(self.shapes)
                shape_count = len([s for s in all_shapes if not s.is_placeholder])
            except Exception:
                pass

            context["description"] = (
                f"Slide Master '{master_name}' defines the foundational design template "
                f"for {layout_count} slide layout(s). Contains {placeholder_count} default "
                f"placeholders and {shape_count} non-placeholder shapes."
            )

            context["role"] = "Foundation of the slide design inheritance hierarchy"
            context["design_impact"] = (
                "All slide layouts and slides inherit design elements, placeholder properties, "
                "and theme settings from this master. Changes here affect the entire presentation's visual consistency."
            )

            context["key_features"] = [
                f"Manages {layout_count} slide layouts",
                f"Provides {placeholder_count} placeholder templates",
                f"Contains {shape_count} persistent background elements",
                "Defines color mapping from theme",
                "Establishes default text styles"
            ]

            context["common_operations"] = [
                "Modify master placeholders to change default formatting for all slides",
                "Add persistent background elements (logos, graphics) that appear on all slides",
                "Configure color mapping between theme colors and slide elements",
                "Set up default text styles for titles, body text, and other placeholder types",
                "Create new slide layouts based on this master"
            ]

            context["inheritance_explanation"] = (
                "This master is the root of a three-level inheritance hierarchy: "
                "SlideMaster → SlideLayout → Slide. Properties flow down this chain, "
                "with each level able to override inherited values."
            )

        except Exception as e:
            context["_llm_context_error"] = f"Error generating LLM context: {str(e)}"

        return context


class SlideMasters(ParentedElementProxy):
    """Sequence of |SlideMaster| objects belonging to a presentation.

    Has list access semantics, supporting indexed access, len(), and iteration.
    """

    part: PresentationPart  # pyright: ignore[reportIncompatibleMethodOverride]

    def __init__(self, sldMasterIdLst: CT_SlideMasterIdList, parent: Presentation):
        super(SlideMasters, self).__init__(sldMasterIdLst, parent)
        self._sldMasterIdLst = sldMasterIdLst

    def __getitem__(self, idx: int) -> SlideMaster:
        """Provides indexed access, e.g. `slide_masters[2]`."""
        try:
            sldMasterId = self._sldMasterIdLst.sldMasterId_lst[idx]
        except IndexError:
            raise IndexError("slide master index out of range")
        return self.part.related_slide_master(sldMasterId.rId)

    def __iter__(self):
        """Generate each |SlideMaster| instance in the collection, in sequence."""
        for smi in self._sldMasterIdLst.sldMasterId_lst:
            yield self.part.related_slide_master(smi.rId)

    def __len__(self):
        """Support len() built-in function, e.g. `len(slide_masters) == 4`."""
        return len(self._sldMasterIdLst)


class _Background(ElementProxy):
    """Provides access to slide background properties.

    Note that the presence of this object does not by itself imply an
    explicitly-defined background; a slide with an inherited background still
    has a |_Background| object.
    """

    def __init__(self, cSld: CT_CommonSlideData):
        super(_Background, self).__init__(cSld)
        self._cSld = cSld

    @lazyproperty
    def fill(self):
        """|FillFormat| instance for this background.

        This |FillFormat| object is used to interrogate or specify the fill
        of the slide background.

        Note that accessing this property is potentially destructive. A slide
        background can also be specified by a background style reference and
        accessing this property will remove that reference, if present, and
        replace it with NoFill. This is frequently the case for a slide
        master background.

        This is also the case when there is no explicitly defined background
        (background is inherited); merely accessing this property will cause
        the background to be set to NoFill and the inheritance link will be
        interrupted. This is frequently the case for a slide background.

        Of course, if you are accessing this property in order to set the
        fill, then these changes are of no consequence, but the existing
        background cannot be reliably interrogated using this property unless
        you have already established it is an explicit fill.

        If the background is already a fill, then accessing this property
        makes no changes to the current background.
        """
        bgPr = self._cSld.get_or_add_bgPr()
        return FillFormat.from_fill_parent(bgPr)
