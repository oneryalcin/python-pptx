"""Shapes based on the `p:pic` element, including Picture and Movie."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pptx.dml.line import LineFormat
from pptx.enum.shapes import MSO_SHAPE, MSO_SHAPE_TYPE, PP_MEDIA_TYPE
from pptx.shapes.base import BaseShape
from pptx.shared import ParentedElementProxy
from pptx.util import lazyproperty

if TYPE_CHECKING:
    from pptx.oxml.shapes.picture import CT_Picture
    from pptx.oxml.shapes.shared import CT_LineProperties
    from pptx.types import ProvidesPart


class _BasePicture(BaseShape):
    """Base class for shapes based on a `p:pic` element."""

    def __init__(self, pic: CT_Picture, parent: ProvidesPart):
        super(_BasePicture, self).__init__(pic, parent)
        self._pic = pic

    @property
    def crop_bottom(self) -> float:
        """|float| representing relative portion cropped from shape bottom.

        Read/write. 1.0 represents 100%. For example, 25% is represented by 0.25. Negative values
        are valid as are values greater than 1.0.
        """
        return self._pic.srcRect_b

    @crop_bottom.setter
    def crop_bottom(self, value: float):
        self._pic.srcRect_b = value

    @property
    def crop_left(self) -> float:
        """|float| representing relative portion cropped from left of shape.

        Read/write. 1.0 represents 100%. A negative value extends the side beyond the image
        boundary.
        """
        return self._pic.srcRect_l

    @crop_left.setter
    def crop_left(self, value: float):
        self._pic.srcRect_l = value

    @property
    def crop_right(self) -> float:
        """|float| representing relative portion cropped from right of shape.

        Read/write. 1.0 represents 100%.
        """
        return self._pic.srcRect_r

    @crop_right.setter
    def crop_right(self, value: float):
        self._pic.srcRect_r = value

    @property
    def crop_top(self) -> float:
        """|float| representing relative portion cropped from shape top.

        Read/write. 1.0 represents 100%.
        """
        return self._pic.srcRect_t

    @crop_top.setter
    def crop_top(self, value: float):
        self._pic.srcRect_t = value

    def get_or_add_ln(self):
        """Return the `a:ln` element for this `p:pic`-based image.

        The `a:ln` element contains the line format properties XML.
        """
        return self._pic.get_or_add_ln()

    @lazyproperty
    def line(self) -> LineFormat:
        """Provides access to properties of the picture outline, such as its color and width."""
        return LineFormat(self)

    @property
    def ln(self) -> CT_LineProperties | None:
        """The `a:ln` element for this `p:pic`.

        Contains the line format properties such as line color and width. |None| if no `a:ln`
        element is present.
        """
        return self._pic.ln

    def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        """Provide properties for _BasePicture introspection, including crop properties."""
        props = super()._to_dict_properties(include_private, _visited_ids, max_depth, expand_collections, format_for_llm)

        crop_props = {
            "crop_left": self.crop_left,
            "crop_top": self.crop_top,
            "crop_right": self.crop_right,
            "crop_bottom": self.crop_bottom
        }

        for name, value in crop_props.items():
            props[name] = self._format_property_value_for_to_dict(
                value, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
            )

        return props


class Movie(_BasePicture):
    """A movie shape, one that places a video on a slide.

    Like |Picture|, a movie shape is based on the `p:pic` element. A movie is composed of a video
    and a *poster frame*, the placeholder image that represents the video before it is played.
    """

    @lazyproperty
    def media_format(self) -> _MediaFormat:
        """The |_MediaFormat| object for this movie.

        The |_MediaFormat| object provides access to formatting properties for the movie.
        """
        return _MediaFormat(self._pic, self)

    @property
    def media_type(self) -> PP_MEDIA_TYPE:
        """Member of :ref:`PpMediaType` describing this shape.

        The return value is unconditionally `PP_MEDIA_TYPE.MOVIE` in this case.
        """
        return PP_MEDIA_TYPE.MOVIE

    @property
    def poster_frame(self):
        """Return |Image| object containing poster frame for this movie.

        Returns |None| if this movie has no poster frame (uncommon).
        """
        slide_part, rId = self.part, self._pic.blip_rId
        if rId is None:
            return None
        return slide_part.get_image(rId)

    @property
    def shape_type(self) -> MSO_SHAPE_TYPE:
        """Return member of :ref:`MsoShapeType` describing this shape.

        The return value is unconditionally `MSO_SHAPE_TYPE.MEDIA` in this
        case.
        """
        return MSO_SHAPE_TYPE.MEDIA


class Picture(_BasePicture):
    """A picture shape, one that places an image on a slide.

    Based on the `p:pic` element.
    """

    @property
    def auto_shape_type(self) -> MSO_SHAPE | None:
        """Member of MSO_SHAPE indicating masking shape.

        A picture can be masked by any of the so-called "auto-shapes" available in PowerPoint,
        such as an ellipse or triangle. When a picture is masked by a shape, the shape assumes the
        same dimensions as the picture and the portion of the picture outside the shape boundaries
        does not appear. Note the default value for a newly-inserted picture is
        `MSO_AUTO_SHAPE_TYPE.RECTANGLE`, which performs no cropping because the extents of the
        rectangle exactly correspond to the extents of the picture.

        The available shapes correspond to the members of :ref:`MsoAutoShapeType`.

        The return value can also be |None|, indicating the picture either has no geometry (not
        expected) or has custom geometry, like a freeform shape. A picture with no geometry will
        have no visible representation on the slide, although it can be selected. This is because
        without geometry, there is no "inside-the-shape" for it to appear in.
        """
        prstGeom = self._pic.spPr.prstGeom
        if prstGeom is None:  # ---generally means cropped with freeform---
            return None
        return prstGeom.prst

    @auto_shape_type.setter
    def auto_shape_type(self, member: MSO_SHAPE):
        MSO_SHAPE.validate(member)
        spPr = self._pic.spPr
        prstGeom = spPr.prstGeom
        if prstGeom is None:
            spPr._remove_custGeom()  # pyright: ignore[reportPrivateUsage]
            prstGeom = spPr._add_prstGeom()  # pyright: ignore[reportPrivateUsage]
        prstGeom.prst = member

    @property
    def image(self):
        """The |Image| object for this picture.

        Provides access to the properties and bytes of the image in this picture shape.
        """
        slide_part, rId = self.part, self._pic.blip_rId
        if rId is None:
            raise ValueError("no embedded image")
        return slide_part.get_image(rId)

    @property
    def shape_type(self) -> MSO_SHAPE_TYPE:
        """Unconditionally `MSO_SHAPE_TYPE.PICTURE` in this case."""
        return MSO_SHAPE_TYPE.PICTURE

    def _to_dict_identity(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        """Provide identity information for Picture introspection."""
        identity = super()._to_dict_identity(include_private, _visited_ids, max_depth, expand_collections, format_for_llm)

        try:
            img_desc = "unknown image"
            if hasattr(self, 'image') and self.image:
                if self.image.filename:
                    img_desc = self.image.filename
                else:
                    img_desc = f"streamed {self.image.ext} image"
        except (ValueError, AttributeError):
            img_desc = "no embedded image"

        identity["description"] = f"Picture shape displaying: {img_desc}"
        return identity

    def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        """Provide properties for Picture introspection."""
        props = super()._to_dict_properties(include_private, _visited_ids, max_depth, expand_collections, format_for_llm)

        try:
            if hasattr(self, 'image') and self.image and hasattr(self.image, 'to_dict') and max_depth > 0:
                props["image_details"] = self.image.to_dict(
                    include_relationships=True,
                    max_depth=max_depth - 1,
                    include_private=include_private,
                    expand_collections=expand_collections,
                    format_for_llm=format_for_llm,
                    _visited_ids=_visited_ids
                )
            elif hasattr(self, 'image') and self.image:
                props["image_details"] = {
                    "_object_type": "Image",
                    "_summary_or_truncated": True,
                    "filename": getattr(self.image, 'filename', None)
                }
        except (ValueError, AttributeError) as e:
            props["image_details"] = self._create_error_context("image_details", e, "image details access failed")

        props["auto_shape_mask_type"] = self._format_property_value_for_to_dict(
            self.auto_shape_type, include_private, _visited_ids, max_depth - 1, expand_collections, format_for_llm
        )

        if max_depth > 0:
            props["line"] = self.line.to_dict(
                include_relationships=True,
                max_depth=max_depth - 1,
                include_private=include_private,
                expand_collections=expand_collections,
                format_for_llm=format_for_llm,
                _visited_ids=_visited_ids
            )
        else:
            props["line"] = {"_object_type": "LineFormat", "_depth_exceeded": True}

        return props

    def _to_dict_relationships(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        """Provide relationships for Picture introspection."""
        rels = super()._to_dict_relationships(include_private, _visited_ids, max_depth, expand_collections, format_for_llm)

        try:
            if hasattr(self, 'image') and self.image and hasattr(self.image, '_blob'):
                image_part = self.part.related_part(self._pic.blip_rId)
                if hasattr(image_part, 'to_dict'):
                    rels["image_part"] = image_part.to_dict(
                        include_relationships=False,
                        max_depth=0,
                        include_private=include_private,
                        expand_collections=False,
                        format_for_llm=format_for_llm,
                        _visited_ids=_visited_ids
                    )
                else:
                    rels["image_part_ref"] = repr(image_part)
        except (ValueError, KeyError, AttributeError):
            rels["image_part"] = "No related image part found or error."

        return rels

    def _to_dict_llm_context(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        """Provide LLM-friendly context for Picture introspection."""
        context = super()._to_dict_llm_context(include_private, _visited_ids, max_depth, expand_collections, format_for_llm)

        try:
            filename_info = "unknown image"
            crop_info = ""
            mask_info = ""

            if hasattr(self, 'image') and self.image:
                if self.image.filename:
                    filename_info = self.image.filename
                else:
                    filename_info = f"streamed {self.image.ext} image"

            if any([self.crop_left, self.crop_top, self.crop_right, self.crop_bottom]):
                crop_parts = []
                if self.crop_left: crop_parts.append(f"{self.crop_left*100:.1f}% from left")
                if self.crop_top: crop_parts.append(f"{self.crop_top*100:.1f}% from top")
                if self.crop_right: crop_parts.append(f"{self.crop_right*100:.1f}% from right")
                if self.crop_bottom: crop_parts.append(f"{self.crop_bottom*100:.1f}% from bottom")
                crop_info = f" Cropped {', '.join(crop_parts)}."

            if self.auto_shape_type and hasattr(self.auto_shape_type, 'name'):
                mask_info = f" Masked as {self.auto_shape_type.name}."

        except (ValueError, AttributeError):
            filename_info = "no embedded image"

        # Get the existing description from BaseShape and enhance it
        base_description = context.get("description", "")
        enhanced_description = f"{base_description} displaying: {filename_info}.{mask_info}{crop_info}"
        context["description"] = enhanced_description

        # Add summary if not present
        if "summary" not in context:
            context["summary"] = f"Picture: {filename_info}"

        common_operations = context.get("common_operations", [])
        common_operations.extend([
            "change image source (replace with new image)",
            "adjust crop properties (crop_left, crop_top, crop_right, crop_bottom)",
            "set mask shape via auto_shape_type property",
            "modify border line properties"
        ])
        context["common_operations"] = common_operations

        return context


class _MediaFormat(ParentedElementProxy):
    """Provides access to formatting properties for a Media object.

    Media format properties are things like start point, volume, and
    compression type.
    """
