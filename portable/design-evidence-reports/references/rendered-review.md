# Rendered-page review procedure

A short reference for step 6 of `design-evidence-reports`. Capture creation is
not visual review: it proves an image was produced, not that the page is
readable or complete.

## What to hold constant

- the **revision** under review (commit SHA, PR head, deploy id);
- the **URL or artifact path** actually served;
- the **widths**: narrowest realistic reading width, plus the design width;
- the **baseline**: the same page before the change, if one exists.

If any of these is unknown, the review is blocked. Do not substitute the file on
disk for the served page.

If no viewport control is available, render the narrow case in a same-origin
frame of the target width and measure inside it; record that the width was
reached by frame rather than by a native viewport.

## Pass order

1. **Whole page, top to bottom.** Scroll the entire served page at the design
   width. Confirm the page ends where you expect — last figure, footer, closing
   note. Missing tails are the most common capture-pipeline blind spot.
2. **Narrow width, whole page.** Repeat at the narrowest reading width. Look for
   clipped labels, horizontal scroll inside tables, legend collisions,
   annotations that cross the axis or each other, text smaller than body text,
   and figures that shrink below legibility.
3. **Per-figure crop.** For each evidence-bearing figure, capture the figure
   alone at both widths and read it: units visible? cohort named? denominator
   stated? cutoffs marked? uncertainty shown where claimed?
4. **Seam check.** Compare figure text, caption, surrounding prose, source line
   and alt text. Any disagreement in units, cohort or cutoff is a content
   finding, not a copy edit.
5. **Link and interaction check.** Follow every in-page anchor and outbound
   source link from the rendered page; a report that cites a broken source has
   an unverifiable claim.

## Per-finding record

Write findings in this shape so the owner can act without re-deriving them:

```
verdict: content | rendering | design
finding: <one sentence>
evidence: width=<px> element=<selector or position> revision=<sha>
next owner: <owner> — <action>
```

## What counts as evidence

Acceptable:

- the served URL plus the revision it corresponds to;
- a full-page capture at each stated width, with the width recorded;
- a per-figure crop at the narrow width;
- measured DOM geometry (scrollWidth vs clientWidth, element rects) for overflow
  and clipping findings, when image analysis is unavailable.

Not acceptable as evidence of readability:

- a successful build or deploy;
- a screenshot of the editor or source markup;
- a capture taken only at the design width;
- a claim that the page "looks fine" without the width and the element named.
- a rendering verdict that reports "pass" for legibility on the strength of
  geometry alone when no image could be analysed.

## Stop conditions

Stop and report a blocked review when:

- the served page does not match the revision under review;
- the page cannot be loaded at a stated width;
- a source cited by the report is unreachable;
- the evidence required by a figure is absent from the source entirely.

A blocked review is a useful outcome. Report the blocking condition and the
owner, not a partial pass.
