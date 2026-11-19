# Phase 2: the deck's design system

Drafts are made by many agents at once.
One shared design system is what keeps their slides looking like one deck.

## Consult Claude Design

Claude Design lives in Claude as artifact types.
Reach it through the Artifact tool, never through a website.

1. Call the Artifact tool with `action: "quickstart"` and `intent: "slides"`.
   The result carries Claude Design's guidance for slides and lists the design systems this account can use.
   Read all of it.
2. If the user or their team already has a design system (the listing shows it, or they give a link), use that one.
   Read it with `action: "read"`.
3. Otherwise create one for this deck from the Design System type the tool lists, and follow that type's own instructions.
   Base it on what the user told you in phase 1: brand, audience, tone, any template or reference decks.
   If they gave no direction, ask for two or three references they like before inventing a look.

## Make it usable by drafting agents

Write two files in the deck folder.

`<deck>/deck.css`: the design system as CSS variables and base rules on `.slide`.
This is the only CSS that drafts share.

```css
.slide {
  --color-...: ...;   /* every color, named by role */
  --font-...: ...;    /* font families */
  --size-...: ...;    /* type scale, in cqw */
  --space-...: ...;   /* spacing scale, in cqw */
  background: var(--color-...);
  color: var(--color-...);
  font-family: var(--font-...);
}
```

All values come from the design system.
Sizes are in `cqw` (1cqw is 1% of the slide width), so a slide looks the same at any scale.
If the deck has repeating furniture (a footer, a page number, a logo position), define its classes here too, so every agent places it identically.

`<deck>/design.md`: the link to the design system artifact, plus notes an agent needs: when to use each color, the type scale's roles, how dense a slide may be, and what the furniture is.

## Fonts

Pick fonts that exist where the deck will be shown.

- Google Slides can only use fonts from Google Fonts.
- PowerPoint uses fonts installed on the machine that opens the file. Tell the user if the deck's fonts need installing.

Load web fonts in drafts with a Google Fonts `<link>`.

## Gate

Show the user the design system (open the artifact) and one sample slide made with `deck.css`.
Do not start the draft round until they approve the look.
