## Why

The inbox exists to be worked to empty: it is the queue of tasks that have not been sorted yet. But it currently admits any undated task, including 6 that are already filed in a project. A task that has been given a project has been sorted — keeping it in the triage queue is noise in the one view whose whole purpose is to run out.

## What Changes

- Narrow the inbox to tasks that have no date, are not deferred, **and** have no project. Today that takes it from 35 tasks to 29.
- Report in the inbox header how many undated filed tasks are being left out, so they are excluded rather than silently lost. Today that is 6, all in one project.
- Leave the never view **unfiltered by project** on purpose: it keeps listing every undated deferred task, including the one that currently has a project. Recording this as a scenario so the asymmetry between the two dateless views reads as a decision rather than an oversight.
- State explicitly that a task added from the inbox is created unfiled, since that is now what makes it appear there at all.
- This reverses the inbox rule chosen in `2026-09-03-add-inbox-and-date-assignment`, where "undated and not deferred" was picked over "undated and no project". The consequence flagged at the time — that undated filed tasks then belong to no view — is now accepted, with the header count as the mitigation.

## Capabilities

### Modified Capabilities

- `task-board`: the inbox's membership rule narrows to exclude filed tasks; the view header gains the count of what it is hiding; the never view's exemption from that rule and the unfiled-on-add guarantee both become explicit requirements.

## Impact

- `singularity.py` — the inbox's filters in the dateless-bucket query, plus a way to report the filed-but-undated count alongside the listing so the header can show it.
- `main.py` — the header, which currently reports only a task count.
- Counts at time of writing: inbox 35 → 29, with 6 excluded (all in `🔥 Надо грузить дрова!`); never unchanged at 1. These move as the store is used and are recorded as the state that motivated the change, not as fixtures.
- Those 6 tasks become reachable from no view this board offers; they remain reachable in the SingularityApp clients, and the header count is what keeps them from disappearing without trace.
- No new dependencies, and no change to `run.sh`, `requirements.txt`, or `.env`.
- The repo has no automated test suite; verification is through the Textual pilot harness and synthetic tasks.
