# Phase 3: the draft round

Every slide gets four drafts, and all slides are drafted at the same time.

## Spawn one agent per slide

Send all the Agent calls in a single message so they run in parallel.
For a large deck, send them in batches of about eight.
Each agent drafts exactly one slide and writes exactly one file: `<deck>/drafts/<id>/r1.html`.

Give each agent this brief, filled in:

```
You are drafting ONE slide of a deck. Other agents are drafting the other slides right now.
Make 4 clearly different drafts of this slide as HTML, check them, and report back. Do not publish anything.

Slide: <id>, slide <n> of <total>
Content (approved by the user, do not change the meaning or the facts):
<this slide's section of plan.md, in full>

Neighbours, for continuity only: previous slide is "<title>", next slide is "<title>".

Read these first:
- <skill>/references/6-shape-vocabulary.md   (what a draft may contain, and the file format)
- <deck>/design.md and <deck>/deck.css       (this deck's design system: take every style decision from it)
- Claude Design's slide guidance: call the Artifact tool with action "read" and type_url "<the Slides type link from phase 2>".
  Read its section on designing a deck, and use it for design judgment only.
  Ignore its file format, its element list and its pixel sizes: the shape vocabulary and deck.css replace them.
  Do not create or publish an artifact.
<if examples exist> - <skill>/examples/<name>/ for what four distinct drafts look like

The four drafts must differ in layout or in the idea that carries the message, not in small details.
For example: a diagram, a single big number, a comparison, a step by step build.
Name each draft in two or three words (data-name).

Write: <deck>/drafts/<id>/r1.html
Check: <skill>/.venv/bin/python <skill>/scripts/check.py <deck>/drafts/<id>/r1.html <--rules <deck>/rules.json if it exists>
Fix every problem it reports and run it again until all four pass.
Then look at each draft yourself: add --shots <deck>/drafts/<id>/shots to the check command and read the pictures it saves.
Fix anything that looks off: crowding, misalignment, weak hierarchy.

Report: the four draft names with one line each on the idea, any content you could not fit, and anything you were unsure about.
```

## When the agents return

1. Run `check.py` on every draft file yourself. Do not trust a report that says it passed.
2. Look at every slide's four drafts. Send an agent back if its four are variations of one layout.
3. Check the deck as a whole: the furniture sits in the same place on every slide, and neighbouring slides do not all use the same layout.
4. Build and publish the review page (phase 4).
