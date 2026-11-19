---
name: deck-builder
description: Build a slide deck through a draft and review process. Plan the content first, have parallel agents design four drafts of every slide with Claude Design, publish them on one shareable review page, iterate on feedback with four new hybrid drafts until each slide is picked, then build the picked slides as native editable shapes in Google Slides or PowerPoint, or export them to PDF, matching the drafts exactly. Use when the user wants to make, design or build a deck, slides, a presentation, a pitch deck or a talk, or says "deck-builder".
---

# deck-builder

A process for making a deck that a person, or a whole team, shapes by reviewing drafts.
The skill holds no visual style.
Colors, fonts, sizes and spacing come from each deck's own design system and from the drafts the user picks.

## The process

Work through the phases in order.
Each one ends at a gate, and the user opens the gate.
Read the linked reference when you reach a phase, not before.

| Phase | What happens | Gate | Reference |
| --- | --- | --- | --- |
| 1. Plan | Interview the user. Write the outline and the content of every slide. No design yet. | User approves the plan | [references/1-plan.md](references/1-plan.md) |
| 2. Design system | Consult Claude Design and create one design system for this deck. | User approves the look | [references/2-design-system.md](references/2-design-system.md) |
| 3. Draft round | One agent per slide, all in parallel. Each makes four distinct drafts. | Every draft passes `check.py` | [references/3-draft-round.md](references/3-draft-round.md) |
| 4. Review page | Put every slide's four drafts on one page and publish it as an artifact. | User or team gives feedback | [references/4-review-page.md](references/4-review-page.md) |
| 5. Hybrid rounds | For each slide with feedback, four new drafts that combine what was liked. Repeat. | User picks one draft per slide | [references/5-hybrid-rounds.md](references/5-hybrid-rounds.md) |
| 6. Build | Lock the picks and build Google Slides, PowerPoint or PDF from them. | `verify.py` passes | [references/7-build.md](references/7-build.md), [references/8-verify.md](references/8-verify.md) |

Drafts may only use elements that become native shapes.
The list is in [references/6-shape-vocabulary.md](references/6-shape-vocabulary.md), and every drafting agent must read it.

## Rules that hold in every phase

- **Content before design.** Never draft a slide whose content the user has not approved.
- **Always four.** Every round gives four clearly different drafts per slide. Never offer one option, and never four small variations of one layout.
- **All slides at once.** Draft every slide in the same round with parallel agents. Do not go slide by slide.
- **The draft is the truth.** The built deck must match the picked draft exactly. If they differ, fix the build, never the approved draft.
- **Small edits are not rounds.** A wording fix or a nudge on a picked draft is applied directly to the locked file.
- **Never invent style here.** Take every visual decision from the deck's design system or the user's feedback.
- **Ask before anything leaves the machine.** Publishing the review page and creating the Google Slides file both share content. Confirm with the user first.

## Setup, once

```
<skill>/scripts/setup.sh
```

This creates the skill's own virtualenv and browser.
Run every script with `<skill>/.venv/bin/python <skill>/scripts/<name>.py`.
Google Slides also needs a one time sign-in: [references/google-auth.md](references/google-auth.md).

## The deck folder

Keep one folder per deck, wherever the user wants it.

```
<deck>/
  plan.md              the approved outline and content
  slides.json          [{"id": "s01_title", "title": "Title"}, ...] in deck order
  rules.json           optional: checks this team asked for (see 1-plan.md)
  design.md            link to the design system artifact, and its notes
  deck.css             the design system as CSS variables: the only CSS that drafts share
  drafts/<id>/r1.html  round 1 for one slide: four drafts in one file
  drafts/<id>/r2.html  round 2, and so on
  locked/<id>.html     the picked draft for a slide
  review.html          the review page
  spec/                shape specs and reference renders (made by the build)
  out/                 deck.pptx, deck.pdf, gslides.json
```

Slide ids start with the slide number (`s01_`, `s02_`), so sorting them gives deck order.

## Examples

`examples/` holds finished decks made with this process, with their plans, rounds and feedback.
Read one before your first draft round to see what "four distinct drafts" and a good hybrid round look like.
The folder may be empty in a fresh install.
After finishing a deck, offer to save it there as a new example.
