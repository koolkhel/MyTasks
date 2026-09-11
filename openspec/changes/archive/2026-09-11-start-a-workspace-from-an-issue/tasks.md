## 1. The issue's version

- [x] 1.1 Teach `tracker._custom_fields` to keep a field whose value is a list
      of mappings, alongside the single mapping it keeps today, preserving the
      tracker's order. Leave a bare scalar dropped, as now. Verify with a new
      self-contained suite `tests/stub/t_version.py` run as
      `python tests/stub/t_version.py`, against a hand-written payload with
      one single-valued field, one list of two, one empty list, one absent
      field and one scalar: passing is the single and both lists kept in
      order, the scalar still dropped, and every check `ok` with exit 0.
- [x] 1.2 Add the version field's name to `tracker.Config`, read from the
      environment beside the states and the projects, and give `Issue` the
      versions it holds. Verify in `tests/stub/t_version.py` that a payload
      parsed with a field configured yields the versions, with none
      configured yields none, and with a field no issue carries yields none
      -- none of the three reported as an error.
- [x] 1.3 Verify in `tests/stub/t_version.py` that `tracker.ISSUE_FIELDS` is
      the exact string it has always been, and that fetching with a version
      field configured makes the same request as fetching without one.
      Passing is an identical field string, one request either way, the same
      address and the same parameters, which is what makes "reading it costs
      no further request" checkable rather than asserted.
      Written against a pinned literal rather than against HEAD, as first
      drafted: HEAD moves the moment this change lands, so a comparison with
      it would stop meaning anything exactly when it started being needed.

## 2. The row carries it

- [x] 2.1 Before naming anything, check each new name against the classes it
      would live on: `hasattr(main.TaskApp, n)` and
      `hasattr(textual.app.App, n)` for `start_workspace`, `workspace_command`
      and `launch`, plus `grep -n "def <n>(" main.py`. Passing is every name
      unused. Two collisions have landed in this repo before, one of which
      stopped a running app accepting messages.
- [x] 2.2 Carry the issue's versions on its row under a private raw key, the
      way `_tracker_url` and `_tracker_state` already are. Verify in a new
      self-contained suite `tests/stub/t_workspace.py` that a board built with
      stubbed issues shows the versions on the row, and that running
      `tests/stub/t_track2.py` and `tests/stub/t_track3.py` unchanged still
      passes -- the tracker rows are otherwise what they were.

## 3. Starting the program

- [x] 3.1 Add `load_workspace_command` beside the readers for the work
      project, the green tag and the working window, returning the configured
      path or None. Verify in `tests/stub/t_workspace.py` on the absent case
      only, testing the reader with a temporary empty env file: python-dotenv
      finds the real `.env` by walking up from `singularity.py`, so a check
      asserting on a configured path would pass or fail by whose machine ran
      it.
- [x] 3.2 Add one method that takes an argument list and starts it with
      `subprocess.Popen`, no shell, returning nothing and waiting for
      nothing. A suite replaces this method and asserts the list, exactly as
      the link suites replace the opener and assert the address. Verify in
      `tests/stub/t_workspace.py` that the self-contained tier never starts a
      process: the replaced method is the only path, and the suite fails if
      anything reaches `Popen`.
- [x] 3.3 Bind `W` to a new action that starts a workspace from the selected
      tracker row. Verify in `tests/stub/t_workspace.py` the four refusals and
      the one success: a task row, a calendar row and a mail row each say the
      key is for a tracker issue; no program configured says so; a tracker row
      with a program configured hands over an argument list. Read the refusals
      from the status widget's drawn text (`widget.visual.plain`, as
      `tests/stub/t_markup.py` does).
- [x] 3.4 Report a program that cannot be started, distinguishably from one
      that was. Verify in `tests/stub/t_workspace.py` by making the replaced
      launch method raise `FileNotFoundError` and then `PermissionError`, and
      asserting the drawn status says it could not be started in each case and
      differs from the started message.
- [x] 3.5 Verify in `tests/stub/t_workspace.py` that starting a workspace
      sends no request: the stubbed client and the stubbed tracker both record
      what they were asked, and passing is nothing added to either.

- [x] 3.6 Send the started program's three streams to nowhere. Found by
      writing a real program for it: `Popen` inherits the terminal's own file
      descriptors, so one line printed by the program would be painted across
      the task list and nothing in the board could take it back. Verify in
      `tests/stub/t_workspace.py`, by reading `launch`'s own source, that all
      three are `subprocess.DEVNULL`; and by hand, by pointing
      `WORKSPACE_COMMAND` at a program that prints on both streams and seeing
      the board undisturbed.

## 4. The command line

- [x] 4.1 Build the argument list: the configured path, then `--key`,
      `--project` and `--version`, each once. Verify in
      `tests/stub/t_workspace.py` by comparing the captured list exactly --
      element by element, not by substring -- and that nothing resembling a
      branch, a directory or a repository is in it.
- [x] 4.2 Ask the version with `TaskInput`, filled in with the issue's own --
      the first where it names several, empty where it names none. Verify in
      `tests/stub/t_workspace.py` that the prompt opens prefilled for an issue
      with one version, prefilled with the first for an issue with two, and
      empty for an issue with none; that confirming unchanged sends the
      issue's version; and that typing a version the issue never names sends
      that one instead.
- [x] 4.5 Verify in `tests/stub/t_workspace.py` that leaving the prompt, and
      confirming it empty, both start nothing -- the same way `Rename` and
      `Add` already treat an empty answer.
- [x] 4.3 Verify in `tests/stub/t_workspace.py` that a version containing
      characters a shell would treat as syntax arrives at the launch as one
      ordinary argument, unchanged.
- [x] 4.4 Verify in `tests/stub/t_workspace.py`, by reading `main.py`'s own
      source, that `shell=True` appears nowhere and that no formatted or
      concatenated string reaches the launch. The safety property is about
      what the code cannot do, so a check that only inspects one run's
      arguments does not establish it.

## 5. What the board says and shows

- [x] 5.1 Name the key in the key bar and in the help overlay. Verify in
      `tests/stub/t_workspace.py` that the bar's entries include `W` with its
      label and that the help text describes it, the way
      `tests/stub/t_work5.py` checks the project key.
- [x] 5.2 Verify in `tests/stub/t_keys2.py`, unchanged, that `W` and its
      Russian twin are bound and collide with nothing. Passing is that suite's
      existing result, not a new number.

## 6. Verification against a stub

- [x] 6.1 Run the whole self-contained tier with `python tests/run.py` and
      compare against `tests/known_failures.py`. Passing is no suite worse
      than its known result, with `t_version.py` and `t_workspace.py` at full
      marks. Freeze the product code for the run and confirm with
      `shasum main.py singularity.py tracker.py` afterwards, so the run is
      known to be about one version.

## 7. Verification against the live tracker

- [x] 7.1 Separate from the stub runs above, and against the real account: a
      new suite `tests/tracker/t_version6.py`, run as
      `python tests/tracker/t_version6.py`, fetches today's issues with the
      version field configured and asserts that the field is read -- that at
      least one issue carries a version, and that an issue carrying none is
      reported as carrying none rather than failing. Read-only: it makes the
      one fetch the board already makes and writes nothing to the tracker.
      Report counts only -- never an issue key, a summary or a person's name.
- [x] 7.2 In the same suite, assert that the request the board sends with a
      version field configured asks for the same fields it asks for without
      one, against the live endpoint. This is the live half of 1.3: the stub
      shows the code does not change its request, and this shows the account
      answers the same way.
- [x] 7.3 Add `tests/tracker/` to nothing -- the runner discovers suites by
      directory. Verify with `python tests/run.py --list --tracker` that the
      tracker tier's count has risen by one (3 to 4; plain `--list` shows only
      the tier it would run), and with `python tests/run.py --tracker` that
      the tier runs and the new suite passes.
      The tier's other three suites fail on "the calendar could not be read",
      which is this shell having no macOS Calendar grant, not this change:
      `t_label6` gives 12/13 and `t_top6` 8/10 identically in a worktree at
      HEAD, and `t_track6` -- run against a capture taken from that worktree
      minutes earlier -- reports the board's rows unchanged, 22 against 22 in
      the same order, with only its three calendar checks failing.

## 8. Verification by hand

- [x] 8.1 The one thing no suite can show: point `WORKSPACE_COMMAND` at a
      script that does nothing but print its arguments to a file, press `W` on
      a real tracker row, and read the file. Passing is the three arguments in
      the order the spec names them, with the version the tracker actually
      holds for that issue.
      Run against the real tracker with the store substituted -- this key
      never touches the store -- so the only quota spent was the tracker's one
      read. The program really was exec'd: six arguments arrived, matching the
      key, project and version the board held for that row.
