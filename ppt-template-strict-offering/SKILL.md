---
name: ppt-template-strict-offering
description: Create or revise a PowerPoint offering by strictly reusing an existing reference PPT template and replacing only text content while preserving the original slide count, shape count, and layout structure. Use this when the user provides a reference PPT and wants the output to follow it exactly.
---

# PPT Template Strict Offering

Use this skill when the user wants a PowerPoint deliverable that must **strictly follow an existing reference PPT template**.

The goal is **not** to redraw or reinterpret the layout. The goal is to:

1. Copy the reference PPTX.
2. Replace only the intended text content.
3. Keep the original slide structure intact.

## Required inputs

- A **reference PPTX** that defines the layout.
- A **source PPTX or source notes** containing the real solution content.
- A target **output PPTX** path.

## Working rules

- Do **not** rebuild the deck from scratch if the user asks for strict template adherence.
- Do **not** add or remove slides unless the user explicitly asks for that.
- Do **not** change the visual layout structure.
- Prefer replacing text inside existing shapes over creating new shapes.
- If a text replacement risks overflowing, shorten the wording before changing layout.

## Recommended workflow

1. Inspect the reference PPTX.
   - Confirm slide count.
   - Inspect shape count on the target slide(s).
   - Identify which shape indexes contain text that should be replaced.

2. Inspect the source material.
   - Extract the actual solution content.
   - Convert it into concise sales-ready copy that fits the existing boxes.

3. Create the output by copying the reference PPTX.
   - Use the reference file as the starting point.
   - Save to a new output path before editing.

4. Replace text shape-by-shape.
   - Map each target shape index to paragraph strings.
   - Preserve the existing paragraph structure when possible.
   - Prefer paragraph-level replacement over rebuilding the text frame.

5. Verify structure.
   - Slide count in the output should match the reference template.
   - Shape count on each edited slide should match the reference template.
   - Re-read the edited text to confirm replacements landed in the correct shapes.

6. Deliver the output path and call out that the template structure was preserved.

## Preferred implementation approach

Use the bundled helper script:

`replace_template_text.py`

It copies a template PPTX and replaces paragraph text in specified shape indexes while preserving the original slide and shape structure.

## Replacement mapping format

Pass a JSON file with this structure:

```json
{
  "1": ["Title line 1", "Title line 2"],
  "8": [
    "Paragraph one text",
    "Paragraph two text"
  ],
  "14": [
    "Key deliverables: ...",
    "Challenges: ...",
    "Achievements: ..."
  ]
}
```

- Keys are **1-based shape indexes** on the selected slide.
- Values are arrays of paragraph strings.
- Extra existing paragraphs are blanked.

## Example command

```powershell
python "C:\Users\qichen2\.copilot\skills\ppt-template-strict-offering\replace_template_text.py" `
  --template "C:\path\to\reference.pptx" `
  --output "C:\path\to\output.pptx" `
  --replacements "C:\path\to\replacements.json" `
  --slide 1
```

## Notes from the SoftwareOne Azure offering workflow

For the SoftwareOne LLM Deployment on Azure Service case, the reliable pattern was:

- inspect the reference slide first
- inspect the source PPT content second
- keep the original 1-slide / 32-shape structure
- replace only the target text boxes
- verify that output slide count and shape count still matched the template

If PowerPoint COM automation is blocked or unreliable, use `python-pptx` paragraph-level replacement instead of redrawing the page.
