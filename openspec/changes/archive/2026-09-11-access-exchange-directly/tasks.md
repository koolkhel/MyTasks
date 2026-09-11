## 1. The dependency and the configuration

- [x] 1.1 Add the service library to `requirements.txt` and install it in the
      project's venv. Passing: `python -c "import exchangelib"` succeeds in
      that venv, and `pip install -r requirements.txt` from clean resolves it
      as wheels with no compiler.
- [x] 1.2 In `gateway.py`, teach `load_config` the address of the account's
      service and the new names for the identity and the credential command,
      reading the old names as a fallback. Whether reviewing is configured
      SHALL be decided by the address. Passing: the new checks in 4.1 cover
      every case — new names, old names, address missing, credential command
      missing.
- [x] 1.3 Add the address to the board's own `.env` (the user's file, not the
      repository). Passing: `gateway.load_config()` returns a configuration
      naming the service rather than a host and port, checked by 5.1 against
      the live account.

## 2. The conversation

- [x] 2.1 In `gateway.py`, replace what `Server.__enter__` opens: build an
      account against the configured address, and resolve the archive folder's
      identity once, beside the login. Passing: the stub checks in 4.2 show
      one resolution per `Server`, not one per request.
- [x] 2.2 Rewrite `numbers`, `present`, `number` and `holds` as restricted
      queries naming message identities, with no folder selection before them.
      Passing: 4.3 asserts one request per folder per call and the same answers
      the old methods gave, case by case, against the fake.
- [x] 2.3 Rewrite `move` and `mark_seen` to name item identities, marking read
      in one request for a whole set as they do now. Passing: 4.4 asserts one
      request per set, both directions, and that nothing is marked anywhere but
      the archive.
- [x] 2.4 Leave `_talk`, both exceptions, the trace line and the busy
      accounting exactly as they are, and make every new request pass through
      `_talk`. Passing: 4.5 asserts every request appears in the trace with its
      command, its subject, its duration and its outcome, and that no
      credential appears in it — the existing checks in `t_trace.py` still
      pass, adjusted only for the new command names.
- [x] 2.5 Keep `archive` and `restore` byte-for-byte in their structure —
      confirmation before retiring a row, one question per row, the undo
      batching — changing only the requests underneath. Passing: 4.6 replays
      the existing scenarios of both against the fake with unchanged
      expectations.

## 3. What must not change

- [x] 3.1 Confirm `main.py` and `mail.py` are untouched by this change.
      Passing: `git diff --stat` at the end names `gateway.py`,
      `requirements.txt`, the tests and `openspec/`, and neither `main.py` nor
      `mail.py`.

## 4. Stub checks — `tests/stub/`, no credentials, run with `python tests/run.py`

- [x] 4.1 Replace `tests/fakeimap.py` with a fake of the new conversation at
      the same seam (`Server(config, connect=...)`), answering searches, moves
      and flag changes from an in-memory account, and able to fail a named
      request on demand. Passing: it drives every path `t_gateway.py` exercises
      with no server present.
- [x] 4.2–4.6 Carry `tests/stub/t_gateway.py` over to the fake, keeping every
      check's meaning: one resolution per session, one request per folder per
      call, the row economy, the trace, and the archive and restore scenarios.
      **Criterion corrected during the work.** It said "at least its present
      209 checks", which counts runs of a loop rather than behaviours and
      cannot survive a protocol changing: six checks asserted the modified
      UTF-7 encoding of folder names, which no longer exists, and the matrix
      of protocol failures changed shape (six verbs by three failures became
      four requests by four). Counted by check *site* the suite went from 132
      to 134, and every behaviour the old one asserted has a successor except
      those six. The read-only open, which had no successor, was replaced by
      the property it protected: asking a folder anything changes nothing in
      it. Passing: 205 checks, none failing.
- [x] 4.7 Re-run `tests/stub/t_trace.py`, `tests/stub/t_crash.py`,
      `tests/stub/t_busy.py`, `tests/stub/t_mail.py`, `tests/stub/t_mailview.py`
      and `tests/stub/t_promote.py`. Passing: each reports its own total with no
      failures — these read the board's behaviour around the mailbox, which
      this change must not alter.
- [x] 4.8 Prove the new checks are not vacuous: break one request in the fake —
      a search that answers nothing, a move that refuses — and confirm the
      checks that cover it fail, then restore it. Passing: each failure is
      observed before the fix and absent after it.
- [x] 4.9 Run `python tests/run.py` — the self-contained tier. Passing: the
      tier's summary reports every suite passed, none failed, and no suite
      newly counted as known to fail.

## 5. Live checks — `tests/gateway/`, against the real account

- [x] 5.1 Rewrite `tests/gateway/t_gwlive.py` for the new protocol, keeping its
      discipline: a copy of the committed sample mailbox per run, every message
      and task it creates named `zz-`, everything deleted in a `finally`, and
      counts and timings printed but never a subject, sender or folder name.
      Passing: it reports its own total with no failures, and the account holds
      nothing named `zz-` afterwards.
- [x] 5.2 In that suite, measure a real review and record the numbers in the
      run's output: the time to authenticate, to confirm a row of one message,
      and to confirm a folded row. Passing: a folded row costs no more requests
      than a single one — the property the spec states — and the measured time
      for a review is reported rather than assumed.
- [x] 5.3 Run the gateway tier once (`python tests/run.py --gateway`), paced
      away from any other live suite. Passing: the tier reports no failures, no
      throttling, and no `zz-` message or task left on the account — checked
      after the run, not assumed from the suite's own cleanup.
