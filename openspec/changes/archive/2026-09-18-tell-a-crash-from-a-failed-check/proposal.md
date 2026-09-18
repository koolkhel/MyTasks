## Why

The runner printed `FAIL   t_bands   23/23 checks passed` and then, under
"failed; run it alone", nothing. The line reads as a contradiction and is not
one: the mark comes from the pytest process's exit code, the count from a line
the conftest prints at session end whatever that exit was. A part can raise
after its last check -- on the way out of a Textual app, say -- and fail the
pytest item without touching a single check. That is a real failure, and the
runner reported it in the one way that could not be acted on: it showed the
number that is *not* the basis of the verdict and dropped the line that is.

## What Changes

- A suite whose process exited non-zero while every check it made passed is
  marked `CRASH`, not `FAIL`. A check that failed and a part that fell over are
  different kinds of failure -- the second is usually the harness, timing or
  shutdown rather than the board -- and a reader should not have to hunt
  through green checks to learn which they are looking at.
- The cause is put on the line and in the failure block: the part that raised
  and the exception's own last line, taken from pytest's short summary, which
  the runner already captures and today discards because it does not match the
  check-line pattern.
- The known-failures signature of such a run becomes `crash:<Exception>`
  rather than `0`. Today `signature()` counts FAIL check-lines whenever a
  summary was printed, so a crash after the checks signs as "zero checks
  failed" -- an entry recorded from it would describe nothing, and would then
  match any later crash of any kind.
- The verdict itself does not move. The report proposed taking it from the
  checks; that would print `ok` over a part that crashed after its checks, which
  is the one outcome worse than today's.

Recorded assumption: the intermittent crash in `t_bands` itself is not
diagnosed here. Six runs during exploration exited 0, and the tail of the run
that did not was not kept. This change makes the next occurrence name itself.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `test-suite`: "A run says what it did" gains the crash mark and the cause;
  "A suite known to fail is recorded with the reason" gains the signature a
  crash after the checks records as.

## Impact

- `tests/run.py` -- the mark, the cause on the line, the failure block.
- `tests/known_failures.py` -- `signature()`.
- A stub suite exercising the runner's report on synthetic outputs, so the
  three shapes (checks failed, crashed after checks, crashed before a summary)
  are each pinned.
- No product file is touched.
