## 1. Keep the protocol inside the gateway

- [x] 1.1 Add a private helper on `Server` that runs one imaplib call and
      converts what comes out of it: `imaplib.IMAP4.abort` and `OSError` to
      `GatewayUnreachable`, `imaplib.IMAP4.error` to `MoveFailed`, each
      naming the command it was running. Verify by adding cases to
      `tests/stub/t_gateway.py` (stub) that a substituted connection raising
      each of the three from a command leaves the caller holding the gateway's
      own exception; passing means the suite never sees an `imaplib` type
      escape and its total check count rises by the cases added.
- [x] 1.2 Route through it every imaplib call that is not already covered —
      `select`, the FLAGS fetch, `MOVE`, the Message-ID `SEARCH` and the
      `STORE` — wrapping the single call and not the surrounding method body,
      so an unrelated `OSError` in a method is not reported as the mailbox's
      fault. `login` and `logout` stay as they are: `__enter__` already
      converts everything around connect and login, and more usefully than
      the helper would, while `__exit__` swallows a line that drops on the way
      out. Verify in `tests/stub/t_gateway.py` (stub) with one case per verb
      and per failure kind, driven by a connection that raises on that verb
      only; passing means each reports a gateway exception naming that
      command, no `imaplib` type escapes any of them, and login and logout are
      shown covered by their existing handling.
- [x] 1.3 Confirm `Server.__enter__`'s existing conversion still wins for
      connect and login, so a gateway that is down at the start still reports
      "could not be reached" with the host and port rather than a per-command
      message. Verify by the existing unreachable-gateway cases in
      `tests/stub/t_gateway.py` (stub) passing unchanged.
- [x] 1.4 Check that neither mailbox worker in `main.py` needs a wider
      `except` afterwards, and that `main.py` imports no `imaplib`. Verify by
      grep: `imaplib` appears in `gateway.py` only, and the two `except
      (gateway.MoveFailed, gateway.GatewayUnreachable)` clauses are unchanged.

## 2. Write the crash down

- [x] 2.1 Add a crash writer to `journal.py` that takes an exception and
      writes one file, deriving its directory from `journal.PATH` so the
      harness's existing redirection covers it. Name it
      `crash-<UTC to the second>.txt`, taking the next free suffix if that
      path exists. Verify in a new `tests/stub/t_crash.py` (stub) that two
      calls in the same second make two files whose names sort in the order
      they were written.
- [x] 2.2 Render the traceback with `Traceback.from_exception`, finding the
      frames rather than assuming the handed-over exception has them: it does
      not when a framework constructs a wrapper instead of raising it, which
      is exactly what Textual does. Keep Textual's `show_locals=True`,
      `width=None`, `locals_max_length=5`, `suppress=[rich]`, printed through
      a `rich.Console` with colour off. Verify in `tests/stub/t_crash.py`
      (stub) that a crash raised on a worker thread and handed over as an
      object still produces a file naming the exception, its frames, and a
      value held in the deepest frame.
- [x] 2.3 Make the writer unable to make things worse: fall back to
      `traceback.format_exception` without locals if rendering raises, and to
      writing nothing if that fails too, reporting neither. Verify in
      `tests/stub/t_crash.py` (stub) with a frame holding an object whose
      `__repr__` raises, and with the log directory pointed at an unwritable
      path; passing means a file with the exception name in the first case, no
      file and no exception in the second, and the caller returning normally
      in both.
- [x] 2.4 Have `TaskApp` override `App._handle_exception`, write the crash
      file, then call `super()` so the session ends exactly as it does now.
      Verify in `tests/stub/t_crash.py` (stub) by driving the board with a
      worker made to raise: passing means one crash file appears in the
      redirected directory and the app still exits.
- [x] 2.5 Guard the private-API dependency: assert in `tests/stub/t_crash.py`
      (stub) that `_handle_exception` exists on Textual's `App` and that the
      override is reached, so a rename in a future Textual fails a suite
      rather than silently ending crash files. Record the Textual version
      this was built against (8.2.8) in the suite's own comment.

## 3. Point the durable log at it

- [x] 3.1 Write one ERROR line to the operations log when a crash file is
      written, naming the crash file and the exception's **type** and not its
      message — an arbitrary exception's message can carry a subject, which
      that log promises not to hold. Verify in `tests/stub/t_crash.py` (stub)
      that the log line holds the file name and the type, and that a crash
      whose exception message is a planted marker string does not put that
      marker in the operations log while the crash file does hold it.
- [x] 3.2 Confirm the today's-crash signature no longer occurs: a review that
      fails now leaves a matching pair of lines rather than an orphaned
      `starting`. Verify in `tests/stub/t_review.py` (stub) by failing a
      review through the substituted gateway; passing means one `starting`
      line and one ERROR line naming the folder, the count and a duration.

## 4. Keep it out of commits

- [x] 4.1 Update the `logs/` comment in `.gitignore`: it currently says
      identities and folder names, which now understates it — a crash file
      holds whatever the frames held, including subjects, senders and bodies.
      Verify by reading the file; passing means the comment says why the
      directory can never be committed, not merely that it is a log.
- [x] 4.2 Add a root-level ignore for a hand-saved crash file, since a person
      saving a traceback out of the terminal puts it in the working directory
      and one is there now. Verify with `git check-ignore -v` naming a path of
      that shape at the repository root, and with `git status --porcelain`
      showing nothing new to commit.
- [x] 4.3 Assert the exclusion rather than trusting it: a case in
      `tests/stub/t_crash.py` (stub) that asks git itself whether the crash
      file's own directory is ignored. Passing means git reports it ignored,
      naming the rule.
- [x] 4.4 Confirm no suite writes a crash into the real `logs/`: the writer
      derives its directory from `journal.PATH`, which `tests/harness.py`
      already repoints. Verify by running the whole stub tier and then
      checking that `logs/` holds no file created during the run.

## 5. Verification against a stub

- [x] 5.1 Run the full stub tier with `.venv/bin/python tests/run.py`.
      Passing means `t_crash` reports all of its checks passed, `t_gateway`,
      `t_review`, `t_promote` and `t_busy` pass at their raised counts, and
      any other failure is shown pre-existing by running that suite against a
      worktree at HEAD rather than being recorded as passing.
- [x] 5.2 Reproduce today's crash as a stub case: a substituted connection
      that answers the moves and then raises `imaplib.IMAP4.abort` from the
      archive-side `EXAMINE` part way through a multi-message row. In
      `tests/stub/t_review.py` (stub), passing means the row returns to the
      queue, the indicator shows the failure mark, the operations log holds
      one ERROR line, no crash file is written, and the board is still
      running — the whole point being that this failure is no longer a crash.

## 6. Verification against the live account

- [x] 6.1 Run `tests/gateway/t_gwlive.py` against the real account unchanged,
      to confirm the per-command conversion did not change the behaviour of a
      review that succeeds. Passing means its check count is unchanged and one
      message is archived, confirmed and moved back, with the smallest folded
      row used and the restore inside the `try` as it already is.
- [x] 6.2 Add one live case that drops the line mid-operation — shutting the
      socket down under the gateway after the move and before the
      archive-side confirmation, `shutdown` rather than `close` because a
      socket with a `makefile` outstanding keeps its descriptor open on a
      close — and confirm the board reports a failed review, keeps running,
      and writes no crash file. Passing means the messages it had already
      moved are found in the archive and are moved back by the case's own
      cleanup, in a `finally`, so an interrupt still restores them.
