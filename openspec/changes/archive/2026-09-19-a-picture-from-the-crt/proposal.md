## Why

The README's pictures are the board drawn by Textual into an SVG and rendered
by a headless browser: crisp, deterministic, and taken from nothing but the
board itself on invented data. They show the board; they do not show it where
it lives. The board is run in cool-retro-term with the IBM 3278 profile, and
that is what the person who built it wants the first picture to be -- the
phosphor, the scanlines and the curve are the terminal's work, and no
rendering of an SVG can produce them.

## What Changes

- `docs/screenshots.py` gains a `--serve <shot>` mode that runs one of the
  invented boards in a real terminal and holds it there: the same stubbed
  store, the same replaced calendar and tracker, the same marks and cursor
  the pilot applies -- but through `app.run()`, so a terminal emulator can
  draw it. Nothing real is reachable from that window, whatever is typed into
  it: no token is read, no client is built, every source is a stub.
- It gains a `--crt` mode that, for each shot, launches
  `cool-retro-term -p "IBM 3278" … -e <the serve command>`, waits for the
  served board to say it is ready, finds the new window by which window ids
  appeared, captures it with `screencapture -l`, and closes it.
- `pyobjc-framework-Quartz` joins `requirements.txt` under the same darwin
  marker as EventKit, commented as being for the pictures alone: the window
  list is the one thing Python cannot reach without it.
- The README opens with one picture from the CRT. The three crisp pictures
  stay where they are: they are how the README explains marking, the archive
  and an issue's fix version, and thin glyphs do not survive a phosphor bloom
  at README width.
- The specification gains a requirement it never had: what a published picture
  of the board is allowed to be made from.

Recorded assumptions:

- A CRT capture is a frame of an animation -- the profile flickers and jitters
  and the cursor blinks -- so two captures never match byte for byte. Nothing
  diffs the pictures, and the SVG path stays for anything that ever needs to.
- The capture needs the terminal running the script to be allowed Screen
  Recording, which no command can grant. The script says so plainly when the
  capture comes back empty, rather than writing a black picture.
- The served window opens at cool-retro-term's own size and is captured so.
  Making it larger was asked for and attempted four ways -- UI scripting, Qt's
  scale factor, the xterm resize escape, fullscreen -- and each fails as the
  design records. Fullscreen is the one route left and is its own change.
- The new window takes keyboard focus while it is up. Keys pressed then reach
  the stub and nothing else, but they change the picture; keep hands off for
  the few seconds it takes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: one requirement added -- a published picture of the board is
  taken from the board itself, on invented data, and a board served for a
  picture in a real terminal can reach nothing real.

## Impact

- `docs/screenshots.py` -- the two modes, the readiness handshake, the window
  lookup and capture.
- `requirements.txt` -- one darwin-only line.
- A new stub suite, `tests/stub/t_pictures.py`, for what can be checked with
  no terminal and no window: that the served board is the pilot's board (same
  rows, marks, cursor, no client), that the new window is picked from the
  difference of two id sets, that the ready file is written after the cursor
  is placed.
- `README.md` -- the hero image and a line about how it was taken;
  `docs/crt-today.png` -- the picture.
