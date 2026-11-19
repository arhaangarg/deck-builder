# deck-builder

A Claude Code skill for making slide decks by reviewing drafts.
You pick from four drafts of every slide.
Claude builds your picks as real, editable shapes in Google Slides or PowerPoint.

![A finished slide](assets/axis_2.png)

## How it works

![The six steps](assets/process.svg)

1. **Plan.** Claude interviews you and writes the content of every slide. You approve it before any design starts.
2. **Design system.** Claude Design creates one look for the deck: colors, fonts, spacing.
3. **Four drafts.** One agent per slide, all at once. Each makes four different drafts.
4. **Review page.** Every draft goes on one page you can share. You and your team comment.
5. **Hybrid rounds.** "I like the chart in 3A and the layout of 3D" becomes four new drafts. Repeat until you pick one.
6. **Build.** Your picks become native shapes in Google Slides, PowerPoint or PDF, and are checked against the drafts.

The skill holds no style of its own.
Every color, font and size comes from your deck's design system and the drafts you pick.

## Slides made this way

| | |
| --- | --- |
| ![](assets/axis_3.png) | ![](assets/axis_5.png) |
| ![](assets/consulting_3.png) | ![](assets/consulting_10.png) |

## Install

```sh
git clone https://github.com/arhaangarg/deck-builder ~/.claude/skills/deck-builder
~/.claude/skills/deck-builder/scripts/setup.sh
```

Then ask Claude Code:

```
Use deck-builder to make a deck about ...
```

## What you need

- [Claude Code](https://claude.com/claude-code), with artifacts and subagents.
- Python 3.10 or newer.
- For Google Slides: a Google account. See [references/google-auth.md](references/google-auth.md).
- For checking a PowerPoint build: PowerPoint or LibreOffice.

## Good to know

- Drafts use a small set of shapes: boxes, ellipses, lines, arrows, text and images. That is what keeps the built deck exact and editable. See [references/6-shape-vocabulary.md](references/6-shape-vocabulary.md).
- Built text lands within 0.2% of the slide width of the draft.
- Rebuilding a Google Slides deck replaces all of its slides. The skill refuses if someone edited the deck since the last build.

## Status

An early draft.
The build tools are tested.
The full process is still being tested on real decks.

## License

[MIT](LICENSE)
