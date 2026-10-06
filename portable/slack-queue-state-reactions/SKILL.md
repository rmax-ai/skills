---
name: slack-queue-state-reactions
description: >-
  Expose bounded queue state on chat handoff messages with a small derived
  reaction set: a configured waiting marker while an item is queued, a
  configured active marker while it is being worked, and never more than two
  active items globally. Use when picking up, deferring, starting, or
  finishing dispatched work whose origin is a chat message, and when reaction
  state must be reconciled after restart, duplicate delivery, or partial
  failure. The durable queue (issue tracker or queue database) is the source
  of truth; reactions are only a derived, human-visible indicator.
---

# Slack queue-state reactions

Make queue state of dispatched work visible and bounded on the chat message that
handed the work over — without making the chat platform a second source of truth.

## Purpose and invariants

- The durable queue is the source of truth: the tracker issue, the queue
  database record, or the equivalent durable state. Reaction state is
  **derived** from it and is never authorization, never an execution lock, and
  never proof that work started or finished.
- At most **two** active queue items exist globally. A third or later item
  remains waiting; it may become active only after an active item reaches done
  or blocked.
- A capability gap on the reaction rail must degrade to the thread message,
  never to a silent loss of state.

## State model

| State | Reaction mark (configured) | Required thread action |
|---|---|---|
| waiting | timer/hourglass marker | Acknowledge the wait and the expected next check. |
| active | eyes marker | Name the authoritative queue item and the active slot. |
| done | clear active; optional terminal mark | Post terminal evidence in the origin thread. |
| blocked | clear active; optional terminal mark | Post the blocker and next check in the origin thread. |

Transitions:

1. **Queued / waiting** — when an item is accepted but cannot start (at or
   above the active cap, or otherwise parked), add the configured waiting
   marker to the original top-level handoff and state the expected wait or
   next check in the thread.
2. **Start** — when work starts, remove the waiting marker where supported,
   add the configured active marker to the handoff, and state the
   authoritative queue item plus the active slot in the thread. Never enter
   the active state while two items are already active.
3. **Done or blocked (terminal)** — clear the active marker where supported
   and post the terminal state (done evidence, or the blocker and next check)
   in the origin thread. The durable record remains authoritative.

## Concurrency: the two-active cap

- Count active items from durable queue state, not from reaction state — the
  reaction is an indicator, so it can be stale, missing, or unsupported.
- If two items are active, a new item stays waiting even when its own start
  conditions are otherwise met; never start a third.
- The durable count and any platform-visible marks must agree once
  reconciliation has run. Where a runtime configures a different numeric cap
  or slot model, the runtime configuration is authoritative — port this
  protocol, not the numbers it happens to carry.

## Applying reaction state

- Resolve reaction names and any workspace mapping from **runtime
  configuration**, never from hardcoded values in shared or public content.
- Reaction operations are best-effort and capability-gated ("where
  supported"): preflight that the bot identity holds the required reaction
  scopes before relying on marks. When marks are unavailable, the thread
  message still carries the state and the gap is recorded, not hidden.
- Apply marks idempotently: an "already present" result is success; removing a
  missing reaction is success. Never let a reaction failure fail the workflow.

## Reconciliation

After a restart, duplicate delivery, or partial failure, derive the visible
state from durable queue state and repair it idempotently:

| Durable state | Visible marks | Repair |
|---|---|---|
| waiting | waiting mark missing | add waiting mark (best-effort) |
| active | active mark missing while the slot holds | add active mark; thread note if needed |
| active | waiting mark still present | remove waiting mark, add active mark |
| terminal | active mark still present | clear active mark; terminal thread evidence stands |
| any | conflicting or stale marks from an older run | clear the stale mark, re-derive from durable state |

- Reconciliation never starts, restarts, or duplicates work. It only repairs
  the indicator, and running it twice changes nothing.
- A duplicate delivery of the same handoff is a no-op: same item, same state,
  no second start, no second thread notice.

## Entity mentions

- Refer to people, bots, and channels with the platform's entity-mention
  syntax, resolved at runtime — never display-name text. A mention that
  renders as plain text is a defect.
- Keep workspace-specific identifiers (channel IDs, user IDs, raw message
  bodies) out of shared and public content; the mapping lives in private
  runtime configuration.

## Pitfalls

- **Reactions are never authorization.** An active mark does not grant a
  slot, a completion mark does not close a card, and a missing reaction never
  blocks protocol-correct work.
- **Do not create a parallel signaling system** when the platform rail is
  unavailable; degrade to thread messages using the same state vocabulary.
- **Do not count marks you cannot see.** Without read capability, reconcile
  from durable state and the thread record.
- **Never start a third item** because an active one is "probably" close to
  done — only a durable terminal transition opens a slot.

## Validation

Scenario coverage for the state machine — cap enforcement, third-item waiting,
duplicate delivery, restart reconciliation, and transition semantics:
`references/validation-checklist.md`.
