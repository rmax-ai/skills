---
name: probabilistic-agent-evaluation
description: >-
  Measure stochastic agent reliability with repeated trials, calibrated graders,
  explicit uncertainty, and integrated verification evidence.
---

# Probabilistic Agent Evaluation

## Source

This skill operationalizes ADR-0026, *Probabilistic evaluation for agentic
software development at scale*, from
`decisions/0026-probabilistic-evaluation-for-agentic-software-development-at-scale.md`.
The accepted review of `rmax-ai/architecture#18` named this capability as
missing.

## Purpose

Treat evals as probabilistic evidence inside the verification model, not as a
parallel definition of correctness. Evals estimate behavior distributions for
probabilistic components. Tests establish selected deterministic behaviors.
Verification decides whether evidence discharges required claims. Production
evidence checks assumptions under real operating conditions.
Use deterministic gates for deterministic claims and statistical gates for
probabilistic claims. Safety and governance invariants remain hard constraints
even when the surrounding system is stochastic. Evals complement tests and
verification; they do not replace them.

## When to use

Use this skill when behavior can vary across executions, including:

- LLM planning or reasoning;
- tool selection and sequencing;
- retrieval and ranking;
- generated patches or reviews;
- routing among agents or models;
- recovery after partial failure;
- long-running workflows with changing environments.

Use it to plan eval evidence, select affected evals, interpret repeated trials,
or combine probabilistic evidence with deterministic verification.
Do not sample a claim that an exact deterministic check can decide. Use a
compiler, type, schema, property, contract, or executable acceptance check when
it is the lowest layer capable of deciding that claim. Use
`claim-driven-software-verification` for deterministic claim sufficiency.
Do not use an average eval score to excuse a failed deterministic contract or
to relax a zero-tolerance safety or governance invariant. Test placement is
outside this skill's scope.

## Procedure

1. Inspect the existing evaluation infrastructure before proposing a
   mechanism. Check `benchmark-design`, `benchmark-validity-audit`,
   `benchmark-stability-test`, `ground-truth-construction`, and
   `llm-judge-calibration`. Reuse relevant capabilities. Name the specific gap
   before proposing a new harness.
2. Write the claim and the decision the evidence must support. For each
   property, assign a deterministic check if it has an exact answer. Assign
   statistical evaluation if outcomes vary across independent executions.
   Mark safety and governance properties as hard constraints in either case.
3. Define a versioned `EvalTask` with an id, specification, initial
   environment, allowed actions, expected properties, risk class, graders, and
   an optional perturbation family. State the task distribution the result is
   meant to represent.
4. Choose the strongest grader that can decide each property. Prefer compiler,
   type, schema, property, and contract checks; then deterministic programmatic
   graders; bounded heuristics; model-based graders; and human judgment. Use
   the lowest capable layer. Never substitute a model judge for an exact
   deterministic check.
5. Grade the externally observable final state as the primary correctness
   oracle. Use repository contents, build output, tests and contracts,
   compatibility, migration results, deployment state, or user-visible
   behavior as applicable. Grade a trajectory only when process or safety is
   part of the contract, or when the trace is needed for diagnosis.
6. When a trajectory is a contract, name the constraint before running the
   eval. Examples include forbidden access, required approval before privileged
   mutation, repository ownership, mandatory review or migration protocols,
   forbidden destructive actions, and safety or governance tool-use rules.
   Do not fail a valid final state only because its internal trajectory differs.
7. For a model-based judge, use a constrained rubric, pairwise or reference
   comparison, or classification when practical. Calibrate it against
   adjudicated examples with `llm-judge-calibration`. Record its disagreement
   and known limits. Without calibration, judge reliability is unknown; report
   that uncertainty and the cost of relying on an uncalibrated result.
8. Keep hard constraints separate from statistical quality constraints. Gate
   unauthorized mutation, secret disclosure, repository corruption, policy
   bypass, invalid durable state, and required compatibility failures as hard
   failures with zero tolerated failures. Gate task success, retrieval quality,
    review precision/recall, cost, or latency statistically when applicable.
9. Create one `EvalTrial` for each independent execution. Record task and task
   version, agent and model versions, prompt and tool versions, environment
   version, seed or configuration, trace, final state, grader results, cost,
   latency, and a unique trial id. Count independent executions as samples,
   not assertions within one execution.
10. Use a seed only for components that honor that seed. A seeded run does not
    fix an uncontrolled provider, changing model snapshot, tool, or environment.
    When a provider has no controllable seed, identify each trial independently
    and record the full observable environment and version provenance.
11. Aggregate trials into a versioned `EvalRun` for one candidate and baseline.
    Record candidate and baseline versions, suite version, task distribution,
    trial set, aggregate statistics, and gate decision. Keep a trial distinct
    from an eval run.
    Repetition must be explicit, not hidden in test-runner retries.
12. Report the pass rate and reliability metrics that answer the decision:
    `pass@1`, `pass@k`, `pass^k`, success within the permitted retry budget,
    catastrophic failure, forbidden or unnecessary mutation, cost, latency,
    tool calls, and tokens where applicable. For autonomous engineering, give
    `pass@1` and consistency such as `pass^3` more weight than a large
    `pass@10` that only demonstrates eventual search.
13. Decompose pass-rate variance instead of collapsing it into one flake
    number. Report the independent-trial denominator and separate relevant
    sources such as task sampling, agent or model version, prompt, toolchain,
    environment changes, seed control, perturbations, grader reliability,
    recovery, and operational retries. Keep retries visible; they do not turn
    low reliability into a deterministic-looking pass.
14. Compare a candidate with a pinned baseline and report uncertainty. Choose
    and name a justified method, such as confidence bounds, credible intervals,
    sequential tests, or bootstrap intervals. Set sample size from observed
    variance, permitted regression margin, task risk, and the costs of false
    acceptance and false rejection. A single run is not sufficient evidence
    for a probabilistic claim when variance is material.
15. Add dedicated adversarial or negative tasks for high-risk rare failures.
    Do not rely on average pass rate alone to establish those properties.
    State the uncertainty and remaining risk when the trial budget cannot
    resolve the release question.
16. Select execution depth by change scope. On a pull request, run deterministic
    affected verification and a small affected eval slice with a low trial
    count. On merge or main, run broader regression with a moderate count.
    Run broad distributions, perturbations, and fault injection nightly or
    periodically with a higher count. For model, harness, architecture, or
    release changes, run the full benchmark with a meaningful budget and
    baseline comparison.
17. Select affected evals through architectural dependencies:
    changed files -> owning modules -> affected capabilities or contracts ->
    relevant eval suites. Map tasks to stable capability or contract ids where
    possible. Use full-suite execution as escalation for broad or high-risk
    changes, not as the default for every edit.
18. Add realistic perturbations to important eval families when relevant:
    equivalent task wording, irrelevant context, compatible dependency
    versions, transient tool failures, partial responses, timeouts, retries,
    stale observations, concurrent environment changes, and malformed or
    adversarial boundary inputs.
19. Verify the eval harness and agent with known-good outcomes, known-bad
    counterexamples, expected grader decisions, versioned environments,
    replayable failures, grader unit/contract tests, and judge calibration
    where practical. Treat a changed grader as a new benchmark version unless
    compatibility is established.
20. Put claims, deterministic checks, invariants, eval suites, trial budget,
    statistical thresholds, hard constraints, residual risk, and escalation
    policy in one `VerificationPlan` for non-trivial delegated work. Do not
    declare completion because implementation finished or one eval passed.
    Require the planned evidence, or record unavailable evidence and escalate
    its residual risk.
21. Combine both evidence classes in one ACCEPT/REVIEW/REJECT risk decision.
    A deterministic failure normally dominates aggregate eval quality.
    Passing deterministic tests does not justify release when measured
    probabilistic reliability has materially regressed.
22. Feed production incidents, near misses, and user failures back into
    verification. Minimize and classify each failure. Add a deterministic
    regression test for deterministic claims, an invariant for encodable
    properties, an eval task for probabilistic failures, or a perturbation
    family for robustness failures. Rerun affected suites. Production
    monitoring complements, but does not replace, pre-merge evidence.
23. Version and own eval datasets. Keep stable task ids, manifests, capability
    and risk ownership, and source provenance where relevant. Separate
    train/dev/test or equivalent data when optimization against the suite is
    possible. Protect hidden expected outputs, review obsolete or duplicate
    tasks, and use representative weighting. Use held-out or refreshed tasks
    when systems are repeatedly optimized against the benchmark.
24. Control eval cost by information gained per unit cost. Select affected
    suites, cache deterministic setup, sample representative strata, stop
    sequentially when evidence is decisive, and reserve larger trial budgets
    for high-variance or high-risk slices. Run low-cost deterministic graders
    before model judges and deep suites periodically rather than universally.

## Invariants

- Evals estimate distributions; they do not define correctness in parallel to
  verification.
- Deterministic claims use deterministic gates. Probabilistic claims use
  statistical evidence.
- Safety and governance invariants remain hard constraints.
- Independent executions, not assertions within a run, are the sampling unit.
- Statistical results include uncertainty, versions, and relevant provenance.
- Production evidence complements pre-merge verification.
- No universal framework, statistical library, model provider, or benchmark
  repository is prescribed; preserve the evidence model and integration rules.

## Anti-patterns

**Wrong:** Treat one successful execution as proof of probabilistic reliability.
**Right:** Use independent trials, report variance and uncertainty, and size
the sample to the risk and decision margin.

**Wrong:** Sample every claim, including an exact schema or contract check.
**Right:** Use the strongest deterministic check for an exact property and
reserve evals for probabilistic behavior.

**Wrong:** Hide retries or report only a high `pass@10` score.
**Right:** Keep retry counts visible and report first-attempt success and
consistency measures such as `pass@1` and `pass^3`.

**Wrong:** Collapse task, model, prompt, environment, and grader variation into
one flake number.
**Right:** Name the relevant variance sources and report their contribution
separately.

**Wrong:** Treat an uncalibrated model judge as a known-correct oracle.
**Right:** Calibrate against adjudicated examples and report judge uncertainty.

## Verification checklist

- [ ] The claim and release decision are explicit.
- [ ] Exact deterministic properties use deterministic checks.
- [ ] Safety and governance properties remain hard constraints.
- [ ] Existing benchmark and calibration skills were inspected and reused.
- [ ] Any proposed new harness has a named gap.
- [ ] Tasks, trials, runs, graders, and environments are versioned.
- [ ] Independent executions, not assertions, determine sample size.
- [ ] Seed limits and uncontrolled sources of variation are recorded.
- [ ] Pass rate, variance sources, retry behavior, and uncertainty are reported.
- [ ] Sample size reflects variance, margin, risk, and decision costs.
- [ ] High-risk rare failures have adversarial or negative tasks.
- [ ] The grader uses the strongest practical deterministic oracle.
- [ ] Model-based judges are calibrated against adjudicated examples.
- [ ] Deterministic and probabilistic evidence feed one risk decision.
- [ ] Production evidence informs future verification without replacing pre-merge evidence.
- [ ] Residual risk and unavailable evidence are explicit.

## Failure and escalation

Reject a candidate when a required deterministic contract or hard invariant
fails. Do not let an aggregate eval score override that result. Reject or
review a probabilistic regression according to the stated statistical
threshold; do not infer a pass from an inconclusive single run.
If the sample does not resolve the decision, report the uncertainty and
increase the trial budget, narrow the decision to an affected slice, or
escalate for review. If required evidence is unavailable, record it as
unavailable and state the residual risk. Do not claim that implementation or
one passing trial completes verification.
If a model-based judge lacks calibration, report its reliability as unknown
and escalate the decision rather than presenting its result as established
evidence. If task, grader, or environment versions change, preserve the new
version and do not compare it longitudinally until compatibility is
established.

## Handoffs

- Hand off deterministic claim sufficiency to ADR-0023,
  `claim-driven-software-verification`, and test placement to ADR-0025,
  `agentic-test-ownership-placement`. Do not duplicate those decisions.
- Use `benchmark-design` for construct and task distribution;
  `benchmark-validity-audit` for validity; and `benchmark-stability-test`
  for stability under methodological changes.
- Use `ground-truth-construction` to build adjudicated reference sets and
  `llm-judge-calibration` to measure judge reliability against adjudicated
  examples.
