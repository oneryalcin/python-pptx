### **Project Vision & System Design: AI-Centric Introspection for `python-pptx`**

**1. The Vision: Empowering AI to Master PowerPoint**

Our goal is to transform `python-pptx` from a powerful programmatic library into an **AI-native toolkit**. We envision a system where a Large Language Model (LLM) can interact with a PowerPoint presentation as if it were a human designer with perfect memory and precision. The LLM should be able to:

*   **See the whole picture:** Understand the layout of a slide at a glance.
*   **Inspect with precision:** Zoom in on any element to understand its every detail.
*   **Understand relationships:** Know that changing a slide master will affect multiple slides.
*   **Reason about properties:** Discern *why* a font is bold—was it set directly, or inherited from a placeholder?
*   **Act surgically:** Generate minimal, correct code to make a specific change.

To achieve this, we are not just adding a feature; we are building an **agentic framework** on top of the existing library. This framework must be efficient, intuitive for an AI to use, and robust against errors.

**2. The Core Interaction Model: A Two-Phase Approach**

An AI agent, like a human, needs to explore before it acts. We will model our introspection system around a two-phase workflow: **Discovery (Wide-Angle View)** and **Inspection (Telescope View)**.

#### **Phase 1: Discovery - The "Wide-Angle" or `tree` View**

The first question an agent asks is, "What's on this slide?" It needs a map of the terrain. We will provide this with a new method, `get_tree()`.

*   **Analogy:** This is like running the `tree` command in a terminal or looking at the "Selection Pane" in PowerPoint. You see the hierarchy, names, and types of objects, but not their deep content.
*   **Function:** `slide.get_tree()`
*   **Output:** A lightweight, hierarchical JSON structure. Each node in the tree will contain:
    *   **Identity:** `_object_type`, `name`, `shape_id`.
    *   **Role:** `shape_type`, `placeholder_type`.
    *   **Location:** `geometry` (left, top, width, height).
    *   **Content Snippet:** A brief summary, e.g., `"Text: 'Annual Report...'"` or `"Image: 'logo.png'"`.
    *   **`access_path`:** This is the **most critical element**. A stable, human-readable string like `"slides[0].shapes[1]"` that the LLM can use to reliably reference this exact object in the next phase.

This "Wide-Angle" view is designed to be **token-efficient**. It gives the LLM a complete structural overview without flooding it with thousands of tokens of detailed formatting data it doesn't need yet.

#### **Phase 2: Inspection - The "Hubble Telescope" or `inspect` View**

Once the agent has identified a target object using its `access_path`, it needs to zoom in for a detailed look. This is where our enhanced `to_dict()` method comes in.

*   **Analogy:** This is like selecting an object in PowerPoint and opening the "Format Shape" pane to see every possible setting.
*   **Function:** `shape.to_dict(fields=[...], trace_inheritance=True)`
*   **Output:** A comprehensive, deep dictionary of the object's state.
*   **Key Features:**
    *   **Precision Querying (`fields`):** The LLM can request *only* the data it needs, e.g., `fields=['properties.fill', 'properties.line.width']`. This solves the over-fetching problem and is the cornerstone of an efficient agentic loop.
    *   **Inheritance Tracing (`trace_inheritance`):** When `True`, the output for a property will be a structured dictionary explaining its origin.
        ```json
        "font": {
          "bold": {
            "value": true,
            "source": "SlideLayout",
            "is_inherited": true
          },
          "italic": {
            "value": false,
            "source": "Direct",
            "is_inherited": false
          }
        }
        ```
    *   **Structured Summaries:** For non-expanded collections, it will provide machine-parsable summaries, e.g., `{"_collection_summary": {"count": 5, "item_type": "Shape"}}`.

This "Telescope" view provides the ground truth for any property, enabling the LLM to make informed decisions and generate precise modification code.

---

### **Definitive FEP Roadmap for AI-Centric Introspection**

This roadmap is prioritized to build the agentic framework first, then expand content coverage.

#### **Tier 1: Foundational Content and Framework (Immediate Priority)**

These FEPs complete the core content coverage and establish the essential agentic framework.

*   **FEP-018: `Table` and `_Cell` Introspection**
    *   **Status:** ✅ **Completed.**
    *   **Impact:** Provided full introspection for tables, the last major non-chart content type. This functionality is now part of our baseline.

*   **FEP-019: Precision Inspection Controls (`to_dict` Enhancement)**
    *   **Status:** ✅ **Completed.**
    *   **Impact:** Solved the data over-fetching problem by adding the `fields` parameter and structured collection summaries. This makes deep inspection efficient and is the "Hubble Telescope" view.

*   **FEP-020: The "Wide-Angle" Tree View (`get_tree`)**
    *   **Status:** ✅ **Completed.**
    *   **Impact:** Implemented the efficient "Discovery" phase of the agentic workflow by adding the `get_tree()` method to container objects. This is the "map of the terrain" for the AI.

#### **Tier 2: Expanding Content Coverage (High Priority)**

With the core framework now in place, we will apply it to the remaining major content type.

*   **FEP-021 (Epic): Chart Introspection**
    *   **Status:** **Next in Queue.**
    *   **Goal:** Make all charting components fully introspectable using the new two-phase framework.
    *   **Strategy:** This will be a multi-PR epic. Each sub-FEP will implement `to_dict()` and contribute to an eventual `chart.get_tree()` representation.
        *   **FEP-21A: Chart Leaf Nodes (`DataLabel`, `Marker`, `Point`)**
        *   **FEP-21B: Chart Data Structure (`Series` and subclasses)**
        *   **FEP-21C: Chart Structural Components (`Plot`, `Legend`, `ChartTitle`)**
        *   **FEP-21D: Chart Axes (`CategoryAxis`, `ValueAxis`, etc.)**
        *   **FEP-21E: Chart Root Object (`Chart`, including `Chart.get_tree()`)**
    *   **Priority:** **HIGH.** This is the largest remaining functional gap.

#### **Tier 3: Advanced Context and Polish (Medium Priority)**

These FEPs provide deeper "why" context and complete the introspection of template elements. They should be tackled after the core content coverage is complete.

*   **FEP-022: Advanced Inheritance Tracing**
    *   **Status:** **Pending.**
    *   **Goal:** Answer the question "Why is this property set this way?".
    *   **Scope:** Introduce a `trace_inheritance=True` parameter to `to_dict()` to show the source of inherited properties.
    *   **Priority:** **MEDIUM.** This is a powerful but complex enhancement for enabling deeper reasoning.

*   **FEP-023: `Theme` and Full `txStyles` Introspection**
    *   **Status:** **Pending.**
    *   **Goal:** Provide complete transparency into the presentation's design theme and default text formatting.
    *   **Scope:** Implement `ThemePart.to_dict()` and a full, structured introspection for the `<p:txStyles>` element on the slide master.
    *   **Priority:** **MEDIUM.** This completes the "template" analysis capabilities.

#### **Tier 4: Moonshots (Future Vision)**

These are high-impact, high-effort features to be considered after the core roadmap is complete.

*   **FEP-024: Visual Rendering (`render_as_image`)**
    *   **Status:** **Future.**
    *   **Goal:** Provide a visual representation of a slide for Vision Language Models (VLMs).
    *   **Scope:** Implement a `slide.render_as_image()` method. This will likely require external dependencies and is a significant undertaking.
    *   **Priority:** **LOW.**

*   **FEP-025 (Ongoing): API Capability Enhancements**
    *   **Status:** **Ongoing.**
    *   **Goal:** Add or enhance `python-pptx` modification APIs based on needs discovered through the introspection framework.
    *   **Scope:** This is not a single FEP but a category of work. For example, if introspection reveals detailed shadow properties, a corresponding FEP would be created to add setters for those properties to `ShadowFormat`.
    *   **Priority:** **As Needed.**

---
*Note on Previously Discussed FEPs:*
*   **Advanced Collection Handling (`expand_first_n`, etc.):** This has been **de-scoped**. The `get_tree()` method (FEP-020) provides a more elegant and powerful solution for discovering and sampling items in large collections, making these extra parameters on `to_dict()` redundant.