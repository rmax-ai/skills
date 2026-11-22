# Behavioral cases: design-evidence-reports

Three isolated cases used to validate `portable/design-evidence-reports`.

**Isolation rule.** The executor receives only the case prompt and the skill under
test. The answer key below is not part of the executor prompt. Each case is
scored against the key afterwards by a separate pass.

**Variant rule.** Case C is run a second time with an *unseen variant*: the
artifact is altered (different artifact name, different number of panels,
different defect position, different widths) while the underlying failure class
is unchanged. A skill that only memorised the first shape fails the variant.

## Case A — inconsistent benchmark units and cohorts

**Artifact.** A one-page benchmark comparison with:

- a bar chart titled "Reasoning accuracy improved 12 points" where run 1 covers
  500 questions and run 2 covers 180 questions drawn from a harder subset;
- a y-axis labelled "score" with no scale, mixing a percentage in one bar and a
  raw count in another;
- a caption reading "same evaluation, later model";
- a footnote excluded from the chart, stating that run 2 dropped questions the
  model failed to parse.

**Prompt to executor.** "Review this benchmark page before we link it from the
release note. Revision: draft-3. Production URL at 1280 px and 390 px."

**Answer key.**

- content: **unsupported**. Cohort changed (500 vs 180, harder subset); the 12
  point delta is not a like-for-like comparison. Denominator for run 2 is not
  the original question set. Unevaluable questions excluded after the fact.
  Units mixed (percentage and count on one axis).
- required next action: either re-run both on one cohort, or restate as two
  separate claims with both cohorts and denominators named; the excluded
  questions must appear as a visible gap, not a footnote.
- rendering: any findings reported must name the width.
- Pass condition: the executor names the cohort change **and** the denominator
  change **and** the mixed units, and does not accept the 12-point claim.
- Fail condition: accepts the delta with a caveat such as "consider noting the
  cohort difference" while still treating the number as valid, or reports only
  axis formatting.

## Case B — incident report, proposed vs observed, mobile defect

**Artifact.** A post-incident report page with:

- a flow diagram with three stages (intake, queue, delivery) drawn once, with a
  legend stating "proposed (solid) / observed (arrow)";
- only two of the three stages have an observed arrow; the deliverable claim in
  the prose is "the pipeline behaved as designed";
- near the bottom of the page, a wide table of timestamps that overflows the
  viewport at 390 px with clipped columns and no scroll affordance;
- event timestamps ordered by when they were reported, not when they occurred.

**Prompt to executor.** "Final review of the incident report before publication.
Revision: sha 4f1c2a. Check it at 1280 and 390."

**Answer key.**

- content: **partially supported**. The prose claim "behaved as designed" is not
  supported by the diagram: the observed route for one stage is absent, so the
  observed behaviour is unknown at that stage, not matching. Proposed and
  observed are conflated in a single drawing.
- rendering: **defect**. The timestamp table overflows at 390 px; columns are
  clipped; no scroll affordance. Reported with width and element.
- design: the timeline orders by knowledge time, not event time; for an incident
  report that ordering misrepresents causality.
- next owner named precisely (content → author / rendering → page owner /
  design → author), with the exact revision.
- Pass condition: all three judgments returned separately; the mobile defect is
  attributed to the *lower page*, not just "mobile looks bad"; the proposed-vs-
  observed conflation is named.
- Fail condition: reports "page renders correctly" because a build passed, or
  only checks the first viewport, or merges all findings into one verdict.

**Unseen variant (B').** Same failure class: the overflow moves to a footnote
region and the missing observed arrow moves to the first stage; widths change to
1440 and 375; artifact renamed. A skill that generalises finds the same three
judgments. A skill keyed to "third panel" or "390" fails.

## Case C — title-only edit must stay small

**Artifact.** The same report as Case B, with one change: the page title changes
from "Incident 2026-11-04: queue saturation" to "Incident 2026-11-04: queue
saturation and recovery". No figure, caption, table or timestamp changes.

**Prompt to executor.** "Small change: title edit only, revision sha 9b2e77.
Ready to publish?"

**Answer key.**

- the review must scale down: a title check plus a single render check.
- the title now asserts "recovery", which is a claim. Because the title asserts
  a result, the recovery claim must be checked against the body; if the body
  does not establish recovery, the title is a content finding.
- the previously existing mobile overflow should be reported as pre-existing and
  explicitly out of scope for this change, not silently re-opened or silently
  dropped.
- Pass condition: proportionate response named explicitly; no full re-audit; if
  the title asserts recovery and the body lacks it, that is the single finding.
- Fail condition: triggers the full evidence audit for a title edit, or approves
  the title without checking the new claim, or omits stating that it stayed
  small.

## Scoring

For each case record: which judgments were returned, whether they were separate,
whether the revision was named, whether the findings matched the key's failure
classes, and the proportionate-response behaviour. Record actual outputs, not a
checklist recital.
