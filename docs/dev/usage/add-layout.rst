Adding and Customizing Slide Layouts
====================================

This page explains how to programmatically create new slide layouts at runtime
and add placeholders to them using ``python-pptx``. This feature allows for
dynamic customization of presentations beyond using pre-defined layouts.

Why Create Layouts Programmatically?
------------------------------------

While most presentations can be built using a standard set of slide layouts
provided in a template, there are scenarios where you might need to:

*   Generate layouts with very specific placeholder arrangements not covered by
    existing templates.
*   Create variations of layouts based on data or user input.
*   Develop applications that allow users to design their own layouts within
    certain parameters.

Example 1: Adding a new blank layout
------------------------------------

You can add a new layout to an existing slide master. Each slide master
maintains its own collection of layouts.

.. code-block:: python

   from pptx import Presentation

   # Load or create a presentation
   prs = Presentation() # Or Presentation("my-template.pptx")

   # Get a slide master (typically the first one)
   slide_master = prs.slide_masters[0]

   # Add a new layout
   # 'base_type' refers to the XML type of the layout (e.g., "blank", "title", "picObj")
   # 'name' is the display name for the layout. If omitted, a default name is provided.
   new_layout = slide_master.slide_layouts.add_layout(
       name="My Custom Blank Layout",
       base_type="blank"
   )

   print(f"Added new layout: {new_layout.name} of type '{new_layout.layout_type}'")

In this example:
  - ``add_layout()`` is called on the ``slide_layouts`` collection of a slide master.
  - ``name``: Sets the user-visible name of the layout (e.g., "My Custom Blank Layout").
  - ``base_type``: Specifies the underlying XML type of the layout. Common values
    include "blank", "title" (Title Slide), "tx" (Title and Content),
    "pic" (Content with Caption), "obj" (generic object), etc. This influences
    how PowerPoint might categorize or treat the layout, but you will typically
    define its structure using placeholders.

Example 2: Adding placeholders to the new layout
------------------------------------------------

Once you have a new ``SlideLayout`` object, you can add placeholders to it.

.. code-block:: python

   from pptx import Presentation
   from pptx.enum.shapes import PP_PLACEHOLDER
   from pptx.util import Inches

   prs = Presentation()
   slide_master = prs.slide_masters[0]

   custom_layout = slide_master.slide_layouts.add_layout(
       name="My Layout with Placeholders",
       base_type="custom" # Using "custom" or any descriptive string for the type
   )

   # Add a Title placeholder
   # idx=0 is typical for a main title
   title_ph = custom_layout.placeholders.add(
       ph_type=PP_PLACEHOLDER.TITLE,
       left=Inches(1.0), top=Inches(0.5),
       width=Inches(8.0), height=Inches(1.0),
       idx=0
   )
   title_ph.name = "Custom Title Placeholder" # Optional: set placeholder name

   # Add a Body Content placeholder
   # idx=1 is common for the primary body/content placeholder
   body_ph = custom_layout.placeholders.add(
       ph_type=PP_PLACEHOLDER.BODY,
       left=Inches(1.0), top=Inches(2.0),
       width=Inches(8.0), height=Inches(4.5),
       idx=1
   )

   # Add a Picture placeholder
   # Using a higher idx value, ensuring it's unique on this layout
   pic_ph = custom_layout.placeholders.add(
       ph_type=PP_PLACEHOLDER.PICTURE,
       left=Inches(1.0), top=Inches(2.0), # Example: Overlapping with body for design
       width=Inches(3.0), height=Inches(2.0),
       idx=10 # Placeholder idx values need not be contiguous
   )

   print(f"Layout '{custom_layout.name}' has {len(custom_layout.placeholders)} placeholders.")

Key parameters for ``add_placeholder()`` (or ``.add()`` alias):
  - ``ph_type``: An enumeration value from ``pptx.enum.shapes.PP_PLACEHOLDER``
    (e.g., ``PP_PLACEHOLDER.TITLE``, ``.BODY``, ``.PICTURE``, ``.CHART``, ``.TABLE``).
  - ``left``, ``top``, ``width``, ``height``: Define the position and size of the
    placeholder. Using ``Inches`` or other EMU-compatible units is recommended.
  - ``idx``: A unique integer ID for this placeholder within the slide layout. This
    ID is used by PowerPoint to identify the placeholder. Standard layouts use
    common idx values (e.g., 0 for title, 1 for body), but custom placeholders
    can use other positive integers. Ensure it's unique per layout.

Example 3: Accessing and Modifying Layout Properties
----------------------------------------------------

You can access properties of the layouts you create or existing ones.

.. code-block:: python

   from pptx import Presentation

   prs = Presentation()
   slide_master = prs.slide_masters[0]

   # Assume 'My Custom Blank Layout' was added as in Example 1
   # Retrieve it by name (if name is unique)
   retrieved_layout = None
   for layout in slide_master.slide_layouts:
       if layout.name == "My Custom Blank Layout":
           retrieved_layout = layout
           break

   # Or, if you just added it:
   # new_layout = slide_master.slide_layouts.add_layout(...)

   if retrieved_layout:
       print(f"Layout Name: {retrieved_layout.name}")
       print(f"Layout Type: {retrieved_layout.layout_type}")

       # Modify the name
       retrieved_layout.name = "Renamed Custom Layout"
       print(f"New Name: {retrieved_layout.name}")
   else:
       # Add it first if running standalone
       retrieved_layout = slide_master.slide_layouts.add_layout(
           name="My Custom Blank Layout", base_type="blank"
       )
       print(f"Layout Name: {retrieved_layout.name}")
       retrieved_layout.name = "Renamed Custom Layout"
       print(f"New Name: {retrieved_layout.name}")


The ``.name`` property of a ``SlideLayout`` is read/write. The ``.layout_type``
property is read-only and reflects the ``type`` attribute set during creation.
The name of a layout (``p:cSld/@name``) is what appears in PowerPoint's UI when
choosing a layout.
The type (``p:sldLayout/@type``) is an XML attribute that helps PowerPoint
categorize the layout (e.g. "title", "blank", "custom").
