---
name: design-evidence-reports
description: >-
  Design or review a visual report (chart, flow, timeline, table, panel, page)
  so its form serves the reader's question without distorting the evidence.
  Use when data, incidents, benchmarks or architecture must become a visual
  artifact, and when a rendered page must be judged before publication.
---

# Design evidence reports

## Purpose

Own the relationship between evidence, visual form, page composition and the
rendered reader experience. Coordinate four different questions that are easy
to collapse into one:

- **content**: is every figure, unit, cohort and denominator supported by the
  cited source, with uncertainty and cutoffs stated?
- **rendering**: does the complete served page render correctly at real widths
  and sizes, including the parts below the fold?
- **design**: does the chosen visual form answer the reader's question, and
  does the page composition stay legible?

Producing the artifact is not reviewing it. A successful capture, a green
build, and a merged commit each prove something narrower than "this report is
correct and readable".

## When to use

Use this skill when the deliverable is a visual artifact whose reading depends
on visual structure:

- a chart, dashboard panel, comparison table or annotated diagram;
- an incident timeline with proposed-vs-observed states;
- a benchmark or trend page where cohorts, units or denominators matter;
- a full served page that carries figures, captions and prose together.

Use it on the **review** side whenever a rendered candidate page is about to be
linked, published or handed off.

Do not use it for:

- deciding whether a claim is true — that is verification or scoring work;
- writing the prose itself — that is the editorial owner's job;
- editing the prose of a report you are only reviewing (see "Proportionate
  response" below).

## Composition with other owners

This skill is a controller, not a replacement. Do not duplicate them.

| Responsibility | Owner |
| --- | --- |
| Prose, argument, revision | technical writing / editorial skill |
| Diagram source, Mermaid syntax | diagram/mermaid skill |
| Build, deploy, link handoff | publishing skill |
| Claim support and citation | verification skill |
| Scoring criteria, rubric | rubric authoring skill |

Load the relevant owner for the actual work; use this skill to state the visual
plan, the evidence constraints, and the review verdict.

## Required inputs

Record these before designing or reviewing. If one is missing, ask for it or
mark the report as blocked — do not infer it:

1. the **reader's question** the report must answer, in one sentence;
2. the **source** (file, dataset, URL, commit) each figure derives from;
3. the **revision** being reviewed (commit SHA, PR head, deploy id);
4. the **rendered target**: URL or artifact plus the widths it will be read at;
5. any **operator exception** in force (see step 5).

## Procedure

### 1. Inspect the actual source and the rendered baseline

Read the source data or document, not a summary of it. Then load the rendered
artifact as it is served — the built page, not the markup on disk.

Capture the baseline before you change anything, including one narrow viewport
and one full-page pass. The baseline is what you compare against; without it you
cannot tell a regression from a pre-existing defect.

### 2. Preserve the evidence contract

Every figure carries a contract. State it explicitly, in the report and in the
figure's visible text:

- **units** and the scale used (percent vs percentage points, per-second vs
  per-minute, log vs linear axes);
- **cohort** — who or what is counted, and when;
- **denominator** — the base of every rate, and whether it is stable across the
  series;
- **cutoffs** — date ranges, exclusions, minimum sample size, stop conditions;
- **maturity** — is the period complete? partial? re-stated later?
- **uncertainty** — interval, sample size, or an explicit "not measured".

Then make the guard binding: a check that only lives in prose, while the chart
plots an unsupported denominator, has not protected anything. The emitted
graphic must carry the same constraint as the text. When the data cannot
support a cohort or denominator, the correct output is either a stated,
narrower claim or a visible gap, never an inferred smooth series.

Do not silently harmonize incompatible things. Two series with different units
on one axis, a rate computed over a changing denominator, or a benchmark whose
cohort changed mid-run are content failures, not styling choices.

### 3. Choose the form from the reader's question

Match the visual form to the question, not to the available tooling or to
what looks impressive:

| Reader's question | Form |
| --- | --- |
| "Which is bigger, and by how much?" | bar or dot plot with a stated common denominator |
| "How did it change over periods?" | line or step chart, cutoffs marked on the axis |
| "Where in a process did it go wrong?" | flow with numbered stages |
| "What happened, in what order, and when was it known?" | timeline, separating event time from knowledge time |
| "Which is correct: what we proposed or what we observed?" | side-by-side or arrowed proposed-vs-observed states |
| "What do these many attributes agree or differ on?" | table, with units in the header and one row per cohort |
| "What is the argument?" | prose, with a small anchoring figure if needed |

Name the question, name the form, and note why the alternative was rejected. A
chart that is accurate but answers a question nobody asked is a design failure.

### 4. Compose the page as a whole

Treat the page as one sequence: title, lede, figures, captions, prose, closing.
Then check the seams:

- **source, figure, caption and accessible text agree.** The caption states the
  same units, cohort and cutoff as the chart; the source line names where the
  number comes from; the alt text describes what the figure shows, not the
  title again.
- **titles are not claims the body cannot support**, and body text does not
  repeat what the caption already says.
- **figures are legible at the smallest served width.** SVG labels, axis
  ticks, legends and table columns must survive the narrow case; if they do
  not, the form is wrong for the medium.
- **the primary claim is reachable without scrolling past decoration.**

### 5. Adapt the form under scoped operator exceptions

A deliberate style choice for one artifact (a density change, an unusual
palette, a tighter grid, a one-off layout) is legitimate. The rule is scope:
the exception applies to the named artifact and revision, is recorded in the
plan or commit message, and does not become a global setting, theme, or
default. Do not hard-code a theme, year, metric or brand into this skill; the
report's context supplies those.

Never carry an exception to another artifact, to the shared template, or to the
active work of another workflow without explicit authorization.

### 6. Inspect the complete served page

Before you start: check that the tooling can render every surface you intend to
judge. If images cannot be analysed, or a width cannot be set, say so in the
verdict and restrict the claims — measured DOM geometry is evidence for
overflow and clipping, not for legibility. Do not report a surface as
"inspected" when only its markup was read.

Review the rendered page, not the capture pipeline. Specifically:

1. Load the **whole** served page and scroll it top to bottom. Capture creation
   proves an image exists; it does not prove the page is readable, complete or
   correct.
2. Review at the **relevant widths** — at minimum the narrowest width the page
   will be read at, plus the design width.
3. Check sections that are easy to miss: the last figure, the footer, footnote
   numbering, overflow inside tables, and content that only appears low on the
   page.
4. On the narrow width, inspect for clipped labels, horizontal scroll,
   overlapping annotation arrows, and images that shrink to unreadable
   proportions.

Report what you actually observed, with the width and the element, not a claim
that the page "rendered fine".

### 7. Return three separate judgments

Do not merge them into a single score. Return:

- **content** — supported / unsupported / partially supported, with the
  specific figure and source for each finding.
- **rendering** — pass / defect list, with width, element and revision.
- **design** — serves the question / misaligned, with the form that would
  serve it better.

End with:

- the **exact revision** judged (commit SHA or deploy id);
- the **next owner** — the actor responsible for the next action, and what the
  action is;
- **explicit non-trigger behavior**: if the change is small (a title edit, a
  typo, a colour tweak with no data change) say so and keep the review small.

State clearly when a report is not ready to publish, and which of the three
judgments is the blocker.

## Proportionate response

Match review depth to the change. A title-only edit gets a title check and a
single render check, not a full evidence audit — unless the title asserts a
number, cohort or result, in which case the claim is content and must be
checked.

Do not rewrite the report's prose while returning a review verdict. Findings go
to the owner named in your verdict.

## Failure modes to catch

- A complete-looking chart built on an inferred cohort or an unstated
  denominator.
- A capture reported as a visual review, with no full-page or narrow-width pass.
- Dense tables and tiny SVG labels passing an overflow check while failing the
  reader.
- A one-off style exception quietly promoted to a default.
- A requested model, theme or metric name that does not match what actually
  produced the artifact.
- Claims of success that confuse produced, reviewed, deployed and adopted.

## Verification

A report is only ready when there is an artifact to point at: the source read,
the baseline captured, the constraints stated, the page inspected at the stated
widths, and three judgments tied to one revision. Record the width, the element
and the revision for each finding. Do not report an exercise as a run.
