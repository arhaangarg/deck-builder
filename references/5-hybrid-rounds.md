# Phase 5: hybrid rounds

Feedback rarely picks a draft outright.
More often the user likes parts of several.
A hybrid round turns that feedback into four new drafts.

## What a hybrid round is

For one slide, the four new drafts must all:

- keep everything the reviewer said they liked
- drop everything the reviewer said they disliked
- follow every instruction the reviewer gave

Within those limits, the four must still be distinct layouts.
A hybrid round is not one merged draft plus three small variations.
It is four different answers to the question "what is the best slide that honours this feedback?"

Example.
The feedback is "I like the visuals above the text like 4D, and the natural word cloud from 4B. The footer has too much empty space."
All four new drafts put visuals above text, use the word cloud, and tighten the footer.
They differ in everything the feedback left open: how the cloud is framed, where the title sits, how the text below is grouped.

## Run it

1. Group the feedback by slide. Quote the reviewer's words, do not paraphrase them.
2. Spawn one agent per slide that needs a round, all in one message.
3. Use the phase 3 brief, with these additions:

```
This is round <N> for this slide. Earlier rounds: <deck>/drafts/<id>/r1.html ... r<N-1>.html
Feedback on the last round, in the reviewer's words:
<quoted feedback, with draft labels>

All four new drafts must keep what was liked, drop what was disliked, and follow every instruction.
They must still be four distinct layouts. Do not reproduce an earlier draft unchanged.
Write: <deck>/drafts/<id>/r<N>.html
```

4. Check the results as in phase 3.
5. Rebuild the review page and publish it again from the same file, so the link stays the same.
6. Tell the user which slides have new drafts.

Slides that are already locked are not touched.
Slides with no feedback keep their current drafts.

## When a slide leaves the loop

A slide is done when the user picks one draft.
Lock it:

```
python scripts/lock.py <deck>/drafts/<id>/r<N>.html --draft <a|b|c|d> --out <deck>/locked/<id>.html
```

The locked file is a copy, so later rounds cannot change it.

## Small edits to a picked draft

A change that does not alter the layout is an edit, not a round: a word, a number, a color swap, moving one element.
Edit `<deck>/locked/<id>.html` directly, run `check.py` on it, and rebuild the review page.

If the user asks for a real layout change on a locked slide, that is a new round.
Run it, and lock the new pick with `--replace`.

## Keep the rounds moving

- Never answer feedback with a single new draft.
- If the same slide reaches a third round, stop and ask the user what is still missing before drafting again.
- Each round, list the open slides and the locked slides, so the user sees progress.
