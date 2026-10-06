# Validation checklist — Slack queue-state reactions

Deterministic scenarios for the protocol's state machine. Each scenario names
the durable precondition, the event, and the required observable outcome. Run
the full list after any change to the protocol or to its runtime mapping and
after any restart of the runtime; every item must pass.

"Mark" means the configured reaction for that state (resolved from runtime
configuration). "Thread" means the originating chat thread of the handoff.

## A. Cap enforcement — no more than two active items

- **A1** Given durable active=0, waiting=1; when the item may start; then it
  becomes active; active count is 1.
- **A2** Given durable active=1, waiting=1; when the waiting item may start;
  then it becomes active; active count is 2 (boundary case).
- **A3** Given durable active=2, waiting=1; when a start attempt occurs; then
  the third item REMAINS waiting, no active mark is added, and active count
  stays 2.
- **A4** Given durable active=2; when one active item reaches done or blocked;
  then at most one waiting item becomes active; the count never exceeds 2 in
  any intermediate step.
- **Reject:** any trace where active count exceeds 2, or where a third item
  starts.

## B. Third-item waiting

- **B1** Given two active items; when a third handoff arrives; then the waiting
  mark is applied to the third handoff and the thread notes the wait and the
  expected next check; the third item does not start.
- **B2** Given two active items and a third waiting; when a duplicate delivery
  of the third handoff arrives; then no state changes, no second notice, no
  start.

## C. Duplicate delivery

- **C1** Given an active item and a re-delivered identical handoff; then no
  second active mark, no parallel work start, and at most one thread notice
  per state change.
- **C2** Given a waiting item and a re-delivered identical handoff; then the
  waiting state is unchanged (idempotent).

## D. Restart / partial-failure reconciliation

- **D1** Durable=waiting, no waiting mark present; after reconciliation the
  waiting mark is present (best-effort) and the thread states the wait.
- **D2** Durable=active, waiting mark still present and active mark missing;
  after reconciliation the waiting mark is removed and the active mark added.
- **D3** Durable=terminal, active mark present; after reconciliation the active
  mark is cleared and the terminal thread evidence is unchanged.
- **D4** Run the D1–D3 reconciliation twice back to back; observables are
  identical (idempotence), and no work was started, restarted, or duplicated
  in any step.

## E. Transition semantics — marks and thread actions

- **E1** waiting→active: waiting mark removed where supported; active mark
  added; thread names the authoritative queue item and the active slot.
- **E2** active→done: active mark cleared where supported; terminal (done)
  evidence posted in the origin thread; durable record authoritative.
- **E3** active→blocked: active mark cleared where supported; blocker and next
  check posted in the origin thread.
- **E4** waiting→waiting (deferral continues): waiting mark present; the
  expected-next-check note refreshed at most once per check.
- **Reject:** any transition performed without the corresponding durable
  transition; any terminal state without thread evidence.

## F. Capability gating and mentions

- **F1** Given the reaction rail reports missing scopes; when a transition
  requires a mark; then the thread action still occurs, the gap is recorded,
  and no workflow step fails or blocks.
- **F2** Given a message must reference a recipient; then the rendered text
  contains the platform entity-mention token for that recipient rather than
  display-name text, and no workspace identifier appears in shared or public
  content.

Scenarios are checkable manually in a live thread and, where a runtime ships
fixtures, executable mechanically against the state model.
