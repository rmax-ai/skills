# Choosing the visual form

A short reference for step 3 of `design-evidence-reports`. The controlling
question is what the reader must decide after reading, not what the data
happens to be shaped like.

## Table of forms

| Reader's question | Form | Minimum evidence requirement | Common distortion |
| --- | --- | --- | --- |
| Which is bigger, by how much? | bar, dot plot | one common denominator, stated | truncated axis inflating a gap |
| How did it change between periods? | line, step chart | cutoffs marked; complete periods distinguished from partial | partial last period plotted as if complete |
| Where in a process did it fail? | numbered flow | each stage attributable to an observation | arrows implying causality not observed |
| What happened and when was it known? | timeline | event time separated from knowledge time | ordering by report date instead of event date |
| Proposed vs observed | paired panel or arrowed states | both states anchored to the same revision or period | arrows drawn without a matching observed value |
| Many attributes across cohorts | table | units in the header; one row per cohort | mixed units inside one column |
| The argument itself | prose | claims carry their own citations | figure substituting for an unsupported claim |

## Worked contrasts

**Aggregate rate vs cohort.** A support page shows "resolution time improved"
from 4.1 to 3.2 days. Reading the source shows the later period excludes
reopened tickets. The rate improved because the denominator narrowed, not
because handling got faster. Correct form: two rates with the denominator
stated in the caption, or a single cohort held constant. The chart is not
wrong about the arithmetic; it is wrong about the claim.

**Units on one axis.** An incident chart plots requests per second and error
count on one vertical axis so they "correlate". The visual correlation is an
artifact of two scales sharing an axis. Correct form: separate panels, or a
rate normalized to a stated denominator.

**Proposed vs observed.** A design review shows an intended flow with the
observed flow. The arrow from "queued" to "delivered" exists in the proposal
but not in the observed trace, where every item passed through a retry state.
Correct form: both flows shown, the divergence marked, the observed state named.
An arrow that only the proposal contains is a design claim, not evidence.

**Rendering failure low on the page.** A three-panel figure renders correctly at
the design width, and at 390 px the third panel's annotation arrows overlap the
axis labels and the legend is clipped. The overflow check passed because the
container scrolls. The reader sees an unreadable figure. Correct form: at the
narrow width the panels stack and the legend moves below the figure, or the
figure is split across two sections. Record the width and the element.

**Distinct literals.** A caption says "the two benchmark runs agree" while one
run reports recall at 0.80 and the other at 0.83 over different question sets.
Agreement is not a property the evidence supports; the cohort changed. Correct
form: one cohort, one number, or a stated difference with both cohorts named.

## Anti-patterns

- A chart whose title asserts a result the body never establishes.
- A caption repeating the title instead of stating units and source.
- Alt text that names the figure rather than describing what it shows.
- A "summary" table whose rows are different cohorts in the same column.
- A trend line drawn across a gap where no data exists.
- A diagram that presents proposed behaviour as observed behaviour.
