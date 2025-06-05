"""Main presentation object."""

from __future__ import annotations

import datetime as dt
from typing import IO, TYPE_CHECKING, cast

from pptx.introspection import IntrospectionMixin
from pptx.shared import PartElementProxy
from pptx.slide import SlideMasters, Slides
from pptx.util import lazyproperty

if TYPE_CHECKING:
    from pptx.oxml.presentation import CT_Presentation, CT_SlideId
    from pptx.parts.presentation import PresentationPart
    from pptx.slide import NotesMaster, SlideLayouts
    from pptx.util import Length


class Presentation(PartElementProxy, IntrospectionMixin):
    """PresentationML (PML) presentation.

    Not intended to be constructed directly. Use :func:`pptx.Presentation` to open or
    create a presentation.
    """

    _element: CT_Presentation
    part: PresentationPart  # pyright: ignore[reportIncompatibleMethodOverride]

    def __init__(self, element: "CT_Presentation", part: "PresentationPart"):
        super().__init__(element, part)
        IntrospectionMixin.__init__(self)

    @property
    def core_properties(self):
        """|CoreProperties| instance for this presentation.

        Provides read/write access to the Dublin Core document properties for the presentation.
        """
        return self.part.core_properties

    @property
    def notes_master(self) -> NotesMaster:
        """Instance of |NotesMaster| for this presentation.

        If the presentation does not have a notes master, one is created from a default template
        and returned. The same single instance is returned on each call.
        """
        return self.part.notes_master

    def save(self, file: str | IO[bytes]):
        """Writes this presentation to `file`.

        `file` can be either a file-path or a file-like object open for writing bytes.
        """
        self.part.save(file)

    @property
    def slide_height(self) -> Length | None:
        """Height of slides in this presentation, in English Metric Units (EMU).

        Returns |None| if no slide width is defined. Read/write.
        """
        sldSz = self._element.sldSz
        if sldSz is None:
            return None
        return sldSz.cy

    @slide_height.setter
    def slide_height(self, height: Length):
        sldSz = self._element.get_or_add_sldSz()
        sldSz.cy = height

    @property
    def slide_layouts(self) -> SlideLayouts:
        """|SlideLayouts| collection belonging to the first |SlideMaster| of this presentation.

        A presentation can have more than one slide master and each master will have its own set
        of layouts. This property is a convenience for the common case where the presentation has
        only a single slide master.
        """
        return self.slide_masters[0].slide_layouts

    @property
    def slide_master(self):
        """
        First |SlideMaster| object belonging to this presentation. Typically,
        presentations have only a single slide master. This property provides
        simpler access in that common case.
        """
        return self.slide_masters[0]

    @lazyproperty
    def slide_masters(self) -> SlideMasters:
        """|SlideMasters| collection of slide-masters belonging to this presentation."""
        return SlideMasters(self._element.get_or_add_sldMasterIdLst(), self)

    @property
    def slide_width(self):
        """
        Width of slides in this presentation, in English Metric Units (EMU).
        Returns |None| if no slide width is defined. Read/write.
        """
        sldSz = self._element.sldSz
        if sldSz is None:
            return None
        return sldSz.cx

    @slide_width.setter
    def slide_width(self, width: Length):
        sldSz = self._element.get_or_add_sldSz()
        sldSz.cx = width

    @lazyproperty
    def slides(self):
        """|Slides| object containing the slides in this presentation."""
        sldIdLst = self._element.get_or_add_sldIdLst()
        self.part.rename_slide_parts([cast("CT_SlideId", sldId).rId for sldId in sldIdLst])
        return Slides(sldIdLst, self)

    # --- Introspection Methods ---

    def _to_dict_identity(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        """Provide identity information specific to this Presentation."""
        identity = super()._to_dict_identity(include_private, _visited_ids, max_depth, expand_collections, format_for_llm)

        # Try to get original filename information
        pkg_file_info = "New presentation (default template)"
        try:
            if hasattr(self.part.package, '_pkg_file') and self.part.package._pkg_file:
                if isinstance(self.part.package._pkg_file, str):
                    pkg_file_info = f"Loaded from: {self.part.package._pkg_file}"
                else:
                    pkg_file_info = "Loaded from a file-like object"
        except Exception:
            pass  # Keep default message

        identity["description"] = f"Root Presentation object. {pkg_file_info}."
        return identity

    def _to_dict_properties(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        """Extract key properties of this Presentation."""
        props = {}

        try:
            # Core Properties - manually extract since CoreProperties doesn't have to_dict yet
            core_props_dict = {}
            cp = self.core_properties

            # List of core property names to extract
            core_prop_names = [
                "author", "category", "comments", "content_status", "created",
                "identifier", "keywords", "language", "last_modified_by",
                "last_printed", "modified", "revision", "subject", "title", "version"
            ]

            for name in core_prop_names:
                try:
                    value = getattr(cp, name)
                    # Handle datetime objects specially
                    if isinstance(value, dt.datetime):
                        core_props_dict[name] = value.isoformat() if value else None
                    else:
                        core_props_dict[name] = self._format_property_value_for_to_dict(
                            value, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
                        )
                except (AttributeError, Exception):
                    core_props_dict[name] = None

            props["core_properties"] = core_props_dict
        except Exception as e:
            props["core_properties"] = self._create_error_context("core_properties", e, "failed to extract core properties")

        try:
            # Slide Dimensions
            props["slide_width"] = self._format_property_value_for_to_dict(
                self.slide_width, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
            )
            props["slide_height"] = self._format_property_value_for_to_dict(
                self.slide_height, include_private, _visited_ids, max_depth, expand_collections, format_for_llm
            )
        except Exception as e:
            props["slide_dimensions"] = self._create_error_context("slide_dimensions", e, "failed to get slide dimensions")

        try:
            # Slides Collection (recursive, FEP-012)
            if expand_collections and max_depth > 0:
                slides_list = []
                for slide in self.slides:
                    try:
                        if hasattr(slide, 'to_dict'):
                            slides_list.append(slide.to_dict(
                                include_relationships=True, max_depth=max_depth-1,
                                include_private=include_private, expand_collections=expand_collections,
                                format_for_llm=format_for_llm, _visited_ids=_visited_ids
                            ))
                        else:
                            slides_list.append({
                                "_object_type": "Slide",
                                "slide_id": getattr(slide, 'slide_id', 'Unknown'),
                                "_no_introspection": True
                            })
                    except Exception:
                        slides_list.append({
                            "_object_type": "Slide",
                            "_depth_exceeded": True
                        })
                props["slides"] = slides_list
            else:
                props["slides"] = f"Collection of {len(self.slides)} slides (not expanded)"
        except Exception as e:
            props["slides"] = self._create_error_context("slides", e, "failed to process slides collection")

        try:
            # Slide Masters Collection (future FEP for SlideMaster.to_dict)
            if expand_collections and max_depth > 0:
                masters_list = []
                for sm in self.slide_masters:
                    try:
                        if hasattr(sm, 'to_dict'):
                            masters_list.append(sm.to_dict(
                                include_relationships=True, max_depth=max_depth-1,
                                include_private=include_private, expand_collections=expand_collections,
                                format_for_llm=format_for_llm, _visited_ids=_visited_ids
                            ))
                        else:
                            masters_list.append({
                                "_object_type": "SlideMaster",
                                "name": getattr(sm, 'name', 'Unknown') if hasattr(sm, 'name') else 'Unknown',
                                "_no_introspection": True
                            })
                    except Exception:
                        masters_list.append({
                            "_object_type": "SlideMaster",
                            "_depth_exceeded": True
                        })
                props["slide_masters"] = masters_list
            else:
                props["slide_masters"] = f"Collection of {len(self.slide_masters)} slide masters (not expanded)"
        except Exception as e:
            props["slide_masters"] = self._create_error_context("slide_masters", e, "failed to process slide masters collection")

        try:
            # Notes Master (future FEP for NotesMaster.to_dict)
            notes_master = self.notes_master
            if notes_master:
                if hasattr(notes_master, 'to_dict') and max_depth > 0:
                    props["notes_master"] = notes_master.to_dict(
                        include_relationships=True, max_depth=max_depth-1,
                        include_private=include_private, expand_collections=expand_collections,
                        format_for_llm=format_for_llm, _visited_ids=_visited_ids
                    )
                else:
                    props["notes_master"] = {
                        "_object_type": "NotesMaster",
                        "_summary_or_truncated": True,
                        "name": getattr(notes_master, 'name', None) if hasattr(notes_master, 'name') else None
                    }
            else:
                props["notes_master"] = None
        except Exception as e:
            props["notes_master"] = self._create_error_context("notes_master", e, "failed to access notes master")

        return props

    def _to_dict_relationships(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        """Extract relationship information for this Presentation."""
        rels = {}

        try:
            # Main document part relationship
            if self.part and hasattr(self.part, 'partname'):
                rels["main_document_part"] = {"partname": str(self.part.partname)}
        except Exception:
            pass

        try:
            # Core properties part relationship
            if self.core_properties and hasattr(self.core_properties, 'part') and hasattr(self.core_properties.part, 'partname'):
                rels["core_properties_part"] = {"partname": str(self.core_properties.part.partname)}
        except Exception:
            pass

        return rels

    def _to_dict_llm_context(self, include_private, _visited_ids, max_depth, expand_collections, format_for_llm):
        """Provide natural language context about this Presentation."""
        context = {}

        # Extract title for description
        title = "Untitled Presentation"
        try:
            if self.core_properties and self.core_properties.title:
                title = self.core_properties.title
        except Exception:
            pass

        # Build description parts
        desc_parts = []
        try:
            slides_count = len(self.slides)
            masters_count = len(self.slide_masters)
            desc_parts.append(f"Presentation: '{title}'. Contains {slides_count} slide(s) and {masters_count} slide master(s)")
        except Exception:
            desc_parts.append(f"Presentation: '{title}'")

        try:
            # Add slide dimensions if available
            if self.slide_width and self.slide_height:
                width_inches = self.slide_width.inches if hasattr(self.slide_width, 'inches') else 'Unknown'
                height_inches = self.slide_height.inches if hasattr(self.slide_height, 'inches') else 'Unknown'
                desc_parts.append(f"Slide dimensions: {width_inches:.2f}\"W x {height_inches:.2f}\"H")
        except Exception:
            pass

        try:
            # Check if notes master exists
            if self.notes_master:
                desc_parts.append("Includes a notes master")
        except Exception:
            pass

        # Join description parts
        context["description"] = ". ".join(desc_parts) + "."
        context["summary"] = context["description"]

        # Common operations
        context["common_operations"] = [
            "access slides (prs.slides)",
            "add a slide (prs.slides.add_slide(...))",
            "access slide masters (prs.slide_masters, prs.slide_master)",
            "access notes master (prs.notes_master)",
            "modify core properties (prs.core_properties.title = ...)",
            "change slide dimensions (prs.slide_width = Inches(...))",
            "save presentation (prs.save(...))"
        ]

        return context

    # -- Tree functionality for FEP-020 --

    def get_tree(self, max_depth=2):
        """Generate a hierarchical tree view of this presentation and its slides.

        This method provides the "Wide-Angle" discovery view for FEP-020,
        allowing AI agents to quickly understand the structure and contents
        of a presentation without loading full object details.

        Args:
            max_depth (int): Maximum depth for recursive tree generation.
                Default 2. Controls how deep the tree traversal goes:
                - 0: Just this presentation node (no children)
                - 1: Presentation + immediate slides (no slide children)
                - 2: Presentation + slides + slide shapes

        Returns:
            dict: Tree representation with structure:
                {
                    "_object_type": "Presentation",
                    "_identity": {"title": "...", "slide_count": 5, ...},
                    "access_path": "",
                    "geometry": None,
                    "content_summary": "Presentation: 'Title' (5 slides, 1 master)",
                    "children": [...] | None
                }

        Example:
            >>> prs = Presentation('sample.pptx')
            >>> tree = prs.get_tree(max_depth=1)
            >>> print(tree['content_summary'])
            "Presentation: 'Annual Report' (12 slides, 1 master)"
        """
        # Root object has no access path prefix
        return self._to_tree_node("", max_depth, _current_depth=0)

    def _to_tree_node_identity(self):
        """Override to provide rich presentation identity for tree node representation."""
        identity = {
            "class_name": "Presentation",
        }

        # Add title from core properties
        try:
            if self.core_properties and self.core_properties.title:
                identity["title"] = self.core_properties.title
        except Exception:
            pass

        # Add slide and master counts
        try:
            identity["slide_count"] = len(self.slides)
            identity["master_count"] = len(self.slide_masters)
        except Exception:
            pass

        # Add slide dimensions
        try:
            if self.slide_width and self.slide_height:
                identity["slide_width"] = f"{self.slide_width.inches:.2f} in"
                identity["slide_height"] = f"{self.slide_height.inches:.2f} in"
        except Exception:
            pass

        return identity

    def _to_tree_node_geometry(self):
        """Override - presentations don't have geometry, return None."""
        return None

    def _to_tree_node_content_summary(self):
        """Override to provide presentation content summary for tree node representation."""
        summary_parts = []

        # Presentation title
        title = "Untitled Presentation"
        try:
            if self.core_properties and self.core_properties.title:
                title = self.core_properties.title
        except Exception:
            pass

        summary_parts.append(f"Presentation: '{title}'")

        # Slide and master counts
        try:
            slide_count = len(self.slides)
            master_count = len(self.slide_masters)

            counts = []
            if slide_count > 0:
                counts.append(f"{slide_count} slide{'s' if slide_count != 1 else ''}")
            if master_count > 0:
                counts.append(f"{master_count} master{'s' if master_count != 1 else ''}")

            if counts:
                summary_parts.append(f"({', '.join(counts)})")
        except Exception:
            pass

        # Slide dimensions hint
        try:
            if self.slide_width and self.slide_height:
                w_in = self.slide_width.inches
                h_in = self.slide_height.inches
                # Only show dimensions if they're not the default 10"x7.5"
                if not (abs(w_in - 10.0) < 0.1 and abs(h_in - 7.5) < 0.1):
                    summary_parts.append(f"[{w_in:.1f}\"×{h_in:.1f}\"]")
        except Exception:
            pass

        return " ".join(summary_parts)

    def _to_tree_node_children(self, access_path, max_depth, current_depth):
        """Override to provide presentation's slides as children."""
        if current_depth > max_depth:
            return None

        children = []

        try:
            # Add slides
            for i, slide in enumerate(self.slides):
                slide_access_path = f"slides[{i}]"
                if hasattr(slide, '_to_tree_node'):
                    child_node = slide._to_tree_node(slide_access_path, max_depth, current_depth + 1)
                    children.append(child_node)
                else:
                    # Fallback for slides without tree node support
                    children.append({
                        "_object_type": "Slide",
                        "_identity": {
                            "slide_id": getattr(slide, 'slide_id', 'unknown'),
                            "class_name": "Slide"
                        },
                        "access_path": slide_access_path,
                        "geometry": None,
                        "content_summary": f"Slide {getattr(slide, 'slide_id', 'unknown')}",
                        "children": None
                    })

        except Exception:
            # If we can't access slides, return empty children list
            pass

        return children if children else None
