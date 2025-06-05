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
                    for ph_idx in self.placeholders.keys()
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
                f"Contains {len(self.shapes)} shape(s) including {len(self.placeholders)} placeholder(s)."
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


class SlideLayout(_BaseSlide):
    """Slide layout object.

    Provides access to placeholders, regular shapes, and slide layout-level properties.
    """

    part: SlideLayoutPart  # pyright: ignore[reportIncompatibleMethodOverride]

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


class SlideMaster(_BaseMaster):
    """Slide master object.

    Provides access to slide layouts. Access to placeholders, regular shapes, and slide master-level
    properties is inherited from |_BaseMaster|.
    """

    _element: CT_SlideMaster  # pyright: ignore[reportIncompatibleVariableOverride]

    @lazyproperty
    def slide_layouts(self) -> SlideLayouts:
        """|SlideLayouts| object providing access to this slide-master's layouts."""
        return SlideLayouts(self._element.get_or_add_sldLayoutIdLst(), self)


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
