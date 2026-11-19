# Phase 1: plan the content

No design happens in this phase.
The goal is a plan the user has approved, slide by slide.

## Interview

Ask until nothing is ambiguous.
Cover at least:

- **Audience and occasion.** Who is in the room, what do they already know, how long is the slot?
- **The one takeaway.** What should the audience believe or do afterwards?
- **Source material.** Papers, documents, data, earlier decks. Read all of it before outlining.
- **Output.** Google Slides, PowerPoint, PDF, or several.
- **Constraints.** A template or brand to follow, slide count, aspect ratio, required slides.
- **Reviewers.** One person or a team? Who has the final pick on each slide?
- **Rules.** Anything the team wants enforced on every slide (see below).

## Write the plan

Write `<deck>/plan.md` with one section per slide:

- the slide's id and working title
- its single message, as one sentence
- the exact content: the words, numbers and visuals that carry the message
- the source of every fact, so it can be checked
- speaker notes, if the user wants them

Write real content, not placeholders.
A drafting agent will see only its own slide's section, so each section must stand alone.
Check every number and quote against the source before showing the plan.

Also write `<deck>/slides.json`, the same outline for the scripts:

```json
[{"id": "s01_title", "title": "Title"}, {"id": "s02_problem", "title": "The problem"}]
```

## Rules file (optional)

Only if the team asked for a rule, write `<deck>/rules.json`.
The skill has no default rules.

```json
{"minText": 0.02, "minPad": 0.01, "banned": ["!"]}
```

- `minText`: smallest text allowed, as a fraction of slide width.
- `minPad`: smallest gap between text and the edge of the box it sits in, as a fraction of slide width.
- `banned`: characters that must not appear in slide text.

## Gate

Show the user the outline (titles and messages), then the full plan.
Do not start phase 2 until they approve it.
If the plan changes later, update `plan.md` first, then redraft only the slides that changed.
