"""Slide and related objects."""

from __future__ import annotations

from typing import IO, TYPE_CHECKING, cast

from pptx.enum.shapes import PROG_ID
from pptx.opc.constants import CONTENT_TYPE as CT
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.opc.package import OpcPackage, XmlPart
from pptx.opc.packuri import PackURI
from pptx.oxml.xmlchemy import BaseOxmlElement
from pptx.oxml.slide import CT_NotesMaster, CT_NotesSlide, CT_Slide, CT_SlideLayout
from pptx.oxml.theme import CT_OfficeStyleSheet
from pptx.parts.chart import ChartPart
from pptx.parts.embeddedpackage import EmbeddedPackagePart
from pptx.slide import NotesMaster, NotesSlide, Slide, SlideLayout, SlideMaster
from pptx.util import lazyproperty

if TYPE_CHECKING:
    from pptx.chart.data import ChartData
    from pptx.enum.chart import XL_CHART_TYPE
    from pptx.media import Video
    from pptx.parts.image import Image, ImagePart


class BaseSlidePart(XmlPart):
    """Base class for slide parts.

    This includes slide, slide-layout, and slide-master parts, but also notes-slide,
    notes-master, and handout-master parts.
    """

    _element: CT_Slide  # Specific part types will override this type hint

    def __init__(self, partname: PackURI, content_type: str, package: OpcPackage, element: BaseOxmlElement):
        super().__init__(partname, content_type, package, element)
        self._cached_max_shape_id: int | None = None

    def get_image(self, rId: str) -> Image:
        """Return an |Image| object containing the image related to this slide by *rId*.

        Raises |KeyError| if no image is related by that id, which would generally indicate a
        corrupted .pptx file.
        """
        return cast("ImagePart", self.related_part(rId)).image

    def get_or_add_image_part(self, image_file: str | IO[bytes]):
        """Return `(image_part, rId)` pair corresponding to `image_file`.

        The returned |ImagePart| object contains the image in `image_file` and is
        related to this slide with the key `rId`. If either the image part or
        relationship already exists, they are reused, otherwise they are newly created.
        """
        image_part = self._package.get_or_add_image_part(image_file)
        rId = self.relate_to(image_part, RT.IMAGE)
        return image_part, rId

    @property
    def name(self) -> str:
        """Internal name of this slide."""
        return self._element.cSld.name

    @property
    def _next_shape_id(self) -> int:
        """Return a unique shape id suitable for use with a new shape.

        The returned id is 1 greater than the maximum shape id used so far in this
        part. If turbo mode is enabled for this part, it uses a cached maximum.
        Shape IDs are unique within a part, usually starting from 1 or 2.
        The spTree element itself often has id="1", so shapes start at 2.
        """
        spTree = self._element.cSld.spTree

        if self._cached_max_shape_id is not None:
            self._cached_max_shape_id += 1
            return self._cached_max_shape_id

        # CT_GroupShape (spTree) already has a robust max_shape_id property
        # that correctly finds the maximum ID among all descendant shapes.
        current_max_id = spTree.max_shape_id
        return current_max_id + 1

    @property
    def turbo_add_enabled(self) -> bool:
        """True if "turbo-add" mode is enabled for this part. Read/Write.

        Enabling this mode caches the current maximum shape ID for the part,
        which can significantly speed up adding many shapes. However, it should
        only be used when a single Part instance is being used to add shapes;
        using multiple Part instances for the same underlying part with turbo
        mode on can lead to shape ID collisions.
        """
        return self._cached_max_shape_id is not None

    @turbo_add_enabled.setter
    def turbo_add_enabled(self, value: bool):
        enable = bool(value)
        spTree = self._element.cSld.spTree
        self._cached_max_shape_id = spTree.max_shape_id if enable else None


class NotesMasterPart(BaseSlidePart):
    """Notes master part.

    Corresponds to package file `ppt/notesMasters/notesMaster1.xml`.
    """

    @classmethod
    def create_default(cls, package):
        """
        Create and return a default notes master part, including creating the
        new theme it requires.
        """
        notes_master_part = cls._new(package)
        theme_part = cls._new_theme_part(package)
        notes_master_part.relate_to(theme_part, RT.THEME)
        return notes_master_part

    @lazyproperty
    def notes_master(self):
        """
        Return the |NotesMaster| object that proxies this notes master part.
        """
        return NotesMaster(self._element, self)

    @classmethod
    def _new(cls, package):
        """
        Create and return a standalone, default notes master part based on
        the built-in template (without any related parts, such as theme).
        """
        return NotesMasterPart(
            PackURI("/ppt/notesMasters/notesMaster1.xml"),
            CT.PML_NOTES_MASTER,
            package,
            CT_NotesMaster.new_default(),
        )

    @classmethod
    def _new_theme_part(cls, package):
        """Return new default theme-part suitable for use with a notes master."""
        return XmlPart(
            package.next_partname("/ppt/theme/theme%d.xml"),
            CT.OFC_THEME,
            package,
            CT_OfficeStyleSheet.new_default(),
        )


class NotesSlidePart(BaseSlidePart):
    """Notes slide part.

    Contains the slide notes content and the layout for the slide handout page.
    Corresponds to package file `ppt/notesSlides/notesSlide[1-9][0-9]*.xml`.
    """

    @classmethod
    def new(cls, package, slide_part):
        """Return new |NotesSlidePart| for the slide in `slide_part`.

        The new notes-slide part is based on the (singleton) notes master and related to
        both the notes-master part and `slide_part`. If no notes-master is present,
        one is created based on the default template.
        """
        notes_master_part = package.presentation_part.notes_master_part
        notes_slide_part = cls._add_notes_slide_part(package, slide_part, notes_master_part)
        notes_slide = notes_slide_part.notes_slide
        notes_slide.clone_master_placeholders(notes_master_part.notes_master)
        return notes_slide_part

    @lazyproperty
    def notes_master(self):
        """Return the |NotesMaster| object this notes slide inherits from."""
        notes_master_part = self.part_related_by(RT.NOTES_MASTER)
        return notes_master_part.notes_master

    @lazyproperty
    def notes_slide(self):
        """Return the |NotesSlide| object that proxies this notes slide part."""
        return NotesSlide(self._element, self)

    @classmethod
    def _add_notes_slide_part(cls, package, slide_part, notes_master_part):
        """Create and return a new notes-slide part.

        The return part is fully related, but has no shape content (i.e. placeholders
        not cloned).
        """
        notes_slide_part = NotesSlidePart(
            package.next_partname("/ppt/notesSlides/notesSlide%d.xml"),
            CT.PML_NOTES_SLIDE,
            package,
            CT_NotesSlide.new(),
        )
        notes_slide_part.relate_to(notes_master_part, RT.NOTES_MASTER)
        notes_slide_part.relate_to(slide_part, RT.SLIDE)
        return notes_slide_part


class SlidePart(BaseSlidePart):
    """Slide part. Corresponds to package files ppt/slides/slide[1-9][0-9]*.xml."""

    @classmethod
    def new(cls, partname, package, slide_layout_part):
        """Return newly-created blank slide part.

        The new slide-part has `partname` and a relationship to `slide_layout_part`.
        """
        slide_part = cls(partname, CT.PML_SLIDE, package, CT_Slide.new())
        slide_part.relate_to(slide_layout_part, RT.SLIDE_LAYOUT)
        return slide_part

    def add_chart_part(self, chart_type: XL_CHART_TYPE, chart_data: ChartData):
        """Return str rId of new |ChartPart| object containing chart of `chart_type`.

        The chart depicts `chart_data` and is related to the slide contained in this
        part by `rId`.
        """
        return self.relate_to(ChartPart.new(chart_type, chart_data, self._package), RT.CHART)

    def add_embedded_ole_object_part(
        self, prog_id: PROG_ID | str, ole_object_file: str | IO[bytes]
    ):
        """Return rId of newly-added OLE-object part formed from `ole_object_file`."""
        relationship_type = RT.PACKAGE if isinstance(prog_id, PROG_ID) else RT.OLE_OBJECT
        return self.relate_to(
            EmbeddedPackagePart.factory(
                prog_id, self._blob_from_file(ole_object_file), self._package
            ),
            relationship_type,
        )

    def get_or_add_video_media_part(self, video: Video) -> tuple[str, str]:
        """Return rIds for media and video relationships to media part.

        A new |MediaPart| object is created if it does not already exist
        (such as would occur if the same video appeared more than once in
         a presentation). Two relationships to the media part are created,
        one each with MEDIA and VIDEO relationship types. The need for two
        appears to be for legacy support for an earlier (pre-Office 2010)
        PowerPoint media embedding strategy.
        """
        media_part = self._package.get_or_add_media_part(video)
        media_rId = self.relate_to(media_part, RT.MEDIA)
        video_rId = self.relate_to(media_part, RT.VIDEO)
        return media_rId, video_rId

    @property
    def has_notes_slide(self):
        """
        Return True if this slide has a notes slide, False otherwise. A notes
        slide is created by the :attr:`notes_slide` property when one doesn't
        exist; use this property to test for a notes slide without the
        possible side-effect of creating one.
        """
        try:
            self.part_related_by(RT.NOTES_SLIDE)
        except KeyError:
            return False
        return True

    @lazyproperty
    def notes_slide(self) -> NotesSlide:
        """The |NotesSlide| instance associated with this slide.

        If the slide does not have a notes slide, a new one is created. The same single instance
        is returned on each call.
        """
        try:
            notes_slide_part = self.part_related_by(RT.NOTES_SLIDE)
        except KeyError:
            notes_slide_part = self._add_notes_slide_part()
        return notes_slide_part.notes_slide

    @lazyproperty
    def slide(self):
        """
        The |Slide| object representing this slide part.
        """
        return Slide(self._element, self)

    @property
    def slide_id(self) -> int:
        """Return the slide identifier stored in the presentation part for this slide part."""
        presentation_part = self.package.presentation_part
        return presentation_part.slide_id(self)

    @property
    def slide_layout(self) -> SlideLayout:
        """|SlideLayout| object the slide in this part inherits appearance from."""
        slide_layout_part = self.part_related_by(RT.SLIDE_LAYOUT)
        return slide_layout_part.slide_layout

    def _add_notes_slide_part(self):
        """
        Return a newly created |NotesSlidePart| object related to this slide
        part. Caller is responsible for ensuring this slide doesn't already
        have a notes slide part.
        """
        notes_slide_part = NotesSlidePart.new(self.package, self)
        self.relate_to(notes_slide_part, RT.NOTES_SLIDE)
        return notes_slide_part


class SlideLayoutPart(BaseSlidePart):
    """Slide layout part.

    Corresponds to package files ``ppt/slideLayouts/slideLayout[1-9][0-9]*.xml``.
    """

    @classmethod
    def new(cls, name: str, slide_layout_type: str, slide_master_part):
        """Return newly-created slide layout part.

        The new slide-layout part is named *name*, has *slide_layout_type* and
        is related to *slide_master_part*.
        """
        package = slide_master_part.package
        partname = package.next_partname("/ppt/slideLayouts/slideLayout%d.xml")

        # ---Call CT_SlideLayout.new() to generate the element---
        sldLayout_elm = CT_SlideLayout.new(name, slide_layout_type)

        slide_layout_part = cls(partname, CT.PML_SLIDE_LAYOUT, package, sldLayout_elm)

        # ---relate to slide master---
        rId = slide_master_part.relate_to(slide_layout_part, RT.SLIDE_LAYOUT)

        # ---update slide master's sldLayoutIdLst---
        sldMaster = slide_master_part._element
        sldLayoutIdLst = sldMaster.get_or_add_sldLayoutIdLst()
        # ---Assuming sldMaster.next_sldLayoutId() provides the unique ID---
        # This might need refinement if next_sldLayoutId is not directly available
        # or if it needs a different invocation.
        # Using a placeholder ID as per subtask instructions, as CT_SlideMaster.next_sldLayoutId()
        # was not found. This will be refined in a later step.
        # The typical range starts from 2147483648.
        new_sldLayoutId = sldLayoutIdLst._add_sldLayoutId(rId=rId)
        # ---Set the unique ID for the sldLayoutId entry---
        new_sldLayoutId.id = slide_master_part._element.next_sldLayoutId_id

        return slide_layout_part

    @lazyproperty
    def slide_layout(self):
        """
        The |SlideLayout| object representing this part.
        """
        return SlideLayout(self._element, self)

    @property
    def slide_master(self) -> SlideMaster:
        """Slide master from which this slide layout inherits properties."""
        return self.part_related_by(RT.SLIDE_MASTER).slide_master


class SlideMasterPart(BaseSlidePart):
    """Slide master part.

    Corresponds to package files ppt/slideMasters/slideMaster[1-9][0-9]*.xml.
    """

    def related_slide_layout(self, rId: str) -> SlideLayout:
        """Return |SlideLayout| related to this slide-master by key `rId`."""
        return self.related_part(rId).slide_layout

    @lazyproperty
    def slide_master(self):
        """
        The |SlideMaster| object representing this part.
        """
        return SlideMaster(self._element, self)
