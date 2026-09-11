## 1. Detaching the program

- [x] 1.1 Before naming anything, check that `start_new_session` is the
      argument `subprocess.Popen` takes on this Python, not one of the older
      spellings: `"start_new_session" in inspect.signature(
      subprocess.Popen).parameters`. Passing an argument Popen does not know
      raises at the call, which is inside a worker and reads as the board
      failing to start a program rather than as a mistake here.
- [x] 1.2 Pass `start_new_session=True` where the board starts the program,
      with the reason beside it: the streams were already sent nowhere, and a
      child that opens the controlling terminal bypasses every one of them.
      Verify with `python tests/stub/t_workspace.py` that its existing checks
      still pass -- the argument list handed over, the refusals, and the
      status line are all unchanged by this.
- [x] 1.3 Add a check to `tests/stub/t_workspace.py`, read off `main.py`'s own
      source in the way the no-shell checks already are, that the call which
      starts a program passes `start_new_session=True`. Passing is the flag
      present in the same call as the three `DEVNULL` streams. A property
      about what the code cannot do is not established by watching one run.
- [x] 1.4 Verify in `tests/stub/t_workspace.py` that a program is still
      started and still reaches the board's own launch method with the same
      argument list: the detaching changes how it is started, not what is
      started, and a check that only looked at the flag would not notice the
      call breaking.

## 2. Verification against a stub

- [x] 2.1 Run the whole self-contained tier with `python tests/run.py` and
      compare against `tests/known_failures.py`. Passing is no suite worse
      than its known result, with `t_workspace.py` at full marks. Freeze the
      product code for the run and confirm with `shasum main.py` afterwards.

## 3. Verification by hand

- [x] 3.1 The half no suite here can show, because no suite here has a
      controlling terminal to be detached from: start a program that tries to
      open `/dev/tty` and write to it, and confirm it cannot. Passing is the
      program's own report that the terminal could not be opened.
      Done without a real terminal after all: `os.forkpty` makes one, and the
      same program run inside it both ways settles it. Started as the board
      started it before, it opened the terminal and wrote on it -- the text
      appears in the terminal's own output. Started as the board starts it
      now, `refused: OSError`. Both directions shown, not just the fixed one.
- [x] 3.2 Then the case that started this: press the key on a tracker issue
      from a terminal whose remote control is *not* reachable by the
      environment -- the arrangement that caused it -- and confirm the board
      is undisturbed. Passing is no help overlay, no moved selection and no
      page opened. This is the one that says the defect is gone rather than
      that the flag is present.
      Run by the person on their own board, in exactly that arrangement --
      the terminal is configured to listen but has not been restarted, so no
      socket exists and nothing exports its address. The board was
      undisturbed: no overlay, no moved selection, nothing opened. The
      launcher's log holds the press against the right issue and then
      `open /dev/tty: device not configured` -- the fallback finding nothing
      instead of finding the board.
