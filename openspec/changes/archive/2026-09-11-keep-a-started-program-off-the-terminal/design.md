## Context

See proposal.md - Why. The requirement is in `specs/task-board/spec.md`.

What the board does today, read from the source:

```python
subprocess.Popen(argv, stdin=subprocess.DEVNULL,
                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
```

Three streams sent nowhere, and the child keeps the board's controlling
terminal. Opening `/dev/tty` gets it back regardless of what it inherited.

The evidence this rests on, gathered in the session that found it:

- The terminal's own remote-control command documents the fallback: given no
  address and no address in the environment, *"messages are sent to the
  controlling terminal for this process"*.
- Run here, with neither, it failed with `open /dev/tty: device not
  configured` -- reaching for the controlling terminal and finding none,
  because this shell has none. A board has one.
- Every symptom reported is one character in the board's own bindings: the
  comma that opens help (the second layout's spelling of `?`), and the
  Cyrillic letters bound to move the cursor and to open a link. A reply read
  as typing produces exactly what was seen: the help overlay, the selection
  one row off, and the wrong issue opened.

## Goals / Non-Goals

Goals:

- A program the board starts cannot reach the board's terminal, whatever it
  tries to open.
- The property is checkable without a terminal.

Non-Goals:

- Fixing the program that did it. That belongs in its own repository, and
  this change is what makes that fix optional rather than load-bearing.
- Severing the mail password command. See below.
- Noticing or reporting that a program tried. There is nothing useful the
  board could say, and the attempt is not the board's business.

## Decisions

### A session of its own, not a longer list of streams

`start_new_session=True` on the call that starts the program. The child gets a
new session and process group and, with them, no controlling terminal -- so
`/dev/tty` is not a thing it can open, and nothing it does can reach the
terminal the board is drawing on.

Alternative considered: passing a pseudo-terminal of the board's own making,
so the program has *a* terminal but not *the* terminal. Rejected: it is a file
descriptor and a reader to look after for no gain, since a program started
this way has nowhere useful to draw anyway.

Alternative considered: leaving it and fixing the program. Rejected as the
whole answer. It would work, and it would mean the board's safety rested on
every program anybody ever configures behaving itself. The board is the thing
with something to protect.

### Why the mail password command is not treated the same way

The board runs one other program: the command that yields the mail password.
It is a different case in the way that matters.

- It is awaited, and its output is captured and used. It is not left running
  alongside the board.
- A credential helper may legitimately need a terminal to ask on. Severing it
  would break a pinentry that asks, and break it in the least debuggable way:
  by making the prompt appear nowhere.

So it keeps its terminal, and the difference is not an oversight. If it ever
needs the same treatment, it needs its own thinking about where a password
prompt is supposed to appear.

### Checked by reading the source

The suite checks the call, not a run: that `start_new_session=True` is passed
where the program is started. A property about what the code cannot do is not
established by watching one run behave.

Demonstrating the detachment itself needs a controlling terminal to be
detached from, which no suite here has. That half is a check by hand, on a
real terminal, and is written down as one.

## Risks / Trade-offs

- **A program that wanted the terminal stops getting it.** That is the point,
  and it is a real behaviour change for anybody who configured a program
  expecting to prompt. → The program has somewhere of its own to say things;
  the spec has said so since it was written.
- **Signals no longer reach the program from the board's terminal.** A new
  session means a hangup on the board's terminal does not carry to it. For a
  program whose job is to open a tab elsewhere, outliving the board is
  correct rather than a leak.
- **The mechanism is explained but not reproduced here.** The fallback is
  documented and the reach for `/dev/tty` was observed; the keystrokes arriving
  were observed by the person, not by me. → The fix does not depend on the
  explanation being complete: detaching removes the whole class, whatever the
  bytes were.

## Migration Plan

None. One argument, no configuration, nothing to undo.

## Open Questions

None.
