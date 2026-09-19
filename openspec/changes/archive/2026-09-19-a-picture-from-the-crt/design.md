## Context

See proposal.md for why. What shapes the approach, all of it checked on this
machine before writing:

- `docs/screenshots.py` already builds each picture's board from invented
  data through the suites' `StubClient`, replaces `ical.fetch` and
  `tracker.fetch`, applies marks and a cursor, and drives it under Textual's
  test pilot to an SVG. The board it builds is the board to serve.
- cool-retro-term takes `-p <profile>`, `-T <title>`, `--workdir <dir>` and
  `-e <command…>` on its command line. `IBM 3278` is one of its built-in
  profiles.
- The board names its own terminal tab `MyTasks` on start, so `-T` does not
  survive: a served window and the person's own board window end up with
  the same title. Windows must be told apart some other way.
- `screencapture -l<id>` captures one window by its CoreGraphics id.
  `CGWindowListCopyWindowInfo` lists on-screen windows with owner name and
  id; the scripting layer (System Events) gives no usable id for
  cool-retro-term's windows. Python reaches CoreGraphics through
  `pyobjc-framework-Quartz`, which is not installed.
- Screen Recording is granted per application and read at process start;
  it was granted to kitty during exploration, after a restart. Unpermitted,
  `screencapture` prints `could not create image` and writes nothing.
- The venv's Python is a framework build and shows up as `Python.app` in
  the window list's owner names when it draws nothing -- irrelevant here,
  since the window that matters is cool-retro-term's.

## Goals / Non-Goals

**Goals:**

- One command remakes every picture, the CRT one included.
- The served board is provably the pilot's board: same construction, same
  marks, same cursor, same guarantee that nothing real is reachable.
- Every decision that can be checked without a window is checked in the
  stub tier.

**Non-Goals:**

- Sizing or positioning the window. Where and how large it opens is where
  and how large it is captured; see the decision below for what was tried.
- Replacing the three SVG pictures. They stay crisp and deterministic; the
  CRT picture is added at the top.
- Making CRT captures reproducible byte for byte. They are frames of an
  animation.

## Decisions

### Serve the same board the pilot drives

`shoot()` today does three things in sequence under the pilot: start the
app, wait for the load, then apply threads, events, marks and the cursor and
repaint. `--serve` reuses the same `stub()` and the same application of
threads, events, marks and cursor, but after mount in a real `app.run()`,
scheduled with `call_later` once the load has settled. The sequence is
extracted into one function, `dress(app, shot)`, that both paths call, so
the served board cannot drift from the pictured one: a suite calls `dress`
under the pilot and checks rows, marks and cursor against what the SVG path
gives.

`--serve` never touches `.env`, never constructs `SingularityClient`, and
sets `mail_config` to None as the pilot path does. Keys pressed in the
window act on the `StubClient`, which records and returns; nothing leaves
the process.

### Readiness by a file, not by a delay

A capture taken before the cursor lands shows the wrong row. `--serve
<shot> --ready <path>` writes the path (empty file) after the cursor is
placed and the repaint has happened; `--crt` polls for it with a bounded
wait before capturing, then removes it. A fixed sleep would be either too
short on a slow start or a wasted wait on a fast one, and would give no
signal at all when the board failed to come up.

### The new window is the one that appeared

Before launching, the window ids owned by cool-retro-term are snapshotted;
after launch, the ids are polled until one appears that was not there, and
that is the window captured. Matching on title would find the person's own
board -- both are `MyTasks` -- and matching on "the newest" has no meaning
in CoreGraphics. The snapshot difference is exact whatever windows are
open.

### The window is cool-retro-term's own size, and every way of changing that was tried

A picture wants the whole board and the whole key bar, and the terminal
opens at 1024x796 -- 76 columns -- which cuts two titles and wraps the key
bar. Four ways of getting a larger grid were tried on the machine, and each
failed for a reason worth keeping:

- **UI scripting.** System Events, addressed by the served process's pid,
  *reports* a resize (`1512x948 -> 2044x1221`) that CoreGraphics shows never
  happened (`1024x796` before and after). The Qt window ignores the request
  and System Events answers from its own model.
- **Qt's scale factor.** `QT_SCALE_FACTOR=1.5` opens the window at 1536x1180,
  exactly 1.5 times -- with the same 76 columns, in glyphs 1.5 times the size.
  The user saw it and said so.
- **The xterm resize escape.** `CSI 8 ; 50 ; 140 t` is dropped: `stty size`
  reads 26x76 before and after.
- **`--fullscreen`.** The window is re-created on a Space of its own, and
  thirteen ids appear with it. This one does work: the id that is on screen
  with the display's own bounds captures whole, every title intact, nothing
  wrapped. But its size is the main display's, not one and a half times the
  window's -- two and a half times on the external monitor the board is
  used with, the rows a short band across the top of an otherwise empty
  screen -- and it switches the person's Space for the seconds it lives.
  Reachable, with a new rule for which window is the one, a wait for the
  transition, and a step to scale the capture down; not what was asked for.

cool-retro-term saves no window geometry, so there is no setting to write
either. What changes the grid is a hand on the window's edge. The picture is
taken at the window's own size; a display-sized one is a separate change,
and fullscreen is the route it has.

### Quartz, in requirements.txt, darwin only

The repository keeps one requirements file on purpose -- `run.sh` leaves a
fresh clone one step from a green run -- and `pytest` is already there for
the suites rather than the board. The Quartz binding follows the same
reasoning, under the same `sys_platform == "darwin"` marker EventKit uses,
with a comment saying it serves the pictures alone. The alternative, a
second requirements file, would be the first split for the sake of one
line.

### Refusal is said, not painted

`screencapture` exits non-zero and writes nothing when the screen may not be
recorded. `--crt` checks for the file and, where it is absent, says that the
terminal running the script needs Screen Recording in System Settings >
Privacy & Security, and that the terminal must be restarted afterwards -- the
same shape of message `calendar_access.py` gives for the calendar. No
picture is written.

### The window is closed by ending the served board

The served process is a child of `--crt`; terminating it ends the board, and
cool-retro-term closes a window whose `-e` command has exited. Nothing sends
keystrokes to the window and nothing quits the application, which may be the
person's own.

## Risks / Trade-offs

- **The profile's flicker lands in the frame.** → A single capture is taken
  after readiness; if a frame catches a flicker, running again is one
  command. Recorded as inherent.
- **The window is 76 columns, which cuts two titles.** → Accepted for this
  change; the crisp pictures show the full rows. Fullscreen is the one route
  to more, and is its own change.
- **The new window takes focus and eats keystrokes.** → Observed: the first
  capture caught the person typing and showed a Someday board with an extra
  mark. Harmless -- the stub alone changes -- but the picture is wrong. The
  script's docstring says to keep hands off for the few seconds it is up.
- **Quartz import fails on a machine without it.** → `--crt` says to install
  the requirements and stops; the SVG path is untouched and needs nothing
  new.
- **cool-retro-term is not installed.** → `--crt` says so and stops; the
  default run (SVG) is unchanged.
- **The served board is started with a real terminal's environment.** → It
  reads no `.env` and builds no client; `t_pictures` asserts the app has a
  `StubClient` and that no `SingularityClient` was constructed.
