## Why

The notifications that decide a working day arrive by mail: a build broke, an
issue moved, a merge request needs a look. None of it is on the board, so the
day is read in one place and the reasons to change it in another.

The board already draws three outside sources it does not own — the task
store, the issue tracker, the calendar — and a mailbox is the fourth. This one
costs less than any of them: the standard library reads a maildir, so there is
no dependency to add, no credential to keep and no network call to make.

Measured on a sample inbox shaped like a corporate one — fifteen messages of
which nine belong to three threads:

```
   one row per message            15 rows
   one row per thread              9 rows
```

Threading came free: the notification systems set the headers for it, and
following them needs no library and no guessing. A view of every message
separately would be a feed rather than a board, and the thread is what makes
it a list a person can read.

## What Changes

- The board reads a maildir at a path named in the environment. Nothing else:
  no server, no credentials, no network. Whatever fills that directory —
  a sync tool, a mail client — is deliberately not the board's business, so
  the choice of mail client stays open.
- Messages are grouped into threads by the headers that exist for it, and a
  thread is one row. The row shows when the newest message arrived, who it is
  from, what it is about, and how many messages are behind it.
- The board reads the folders it is told to read — the mailbox's own inbox
  and any others named — rather than the whole account. What wants processing
  daily is a handful of folders, not everything that has ever arrived.
- The rows appear in the **inbox view**, above the tasks awaiting triage,
  rather than among a day's tasks. A day is a set of commitments; the inbox
  is the queue of things not yet decided about, and mail that must be
  processed daily is exactly that. Mail leads the tasks there because it is
  time-ordered and perishable where an undated task waits indefinitely.
- A thread's links can be opened, and where its text names an issue in a
  configured tracker project, that issue can be opened — both through the
  machinery already shipped for tasks.
- Every key that writes refuses on a mail row, as it does on a calendar event
  and a tracker issue. The board reads the mailbox and does not own it.
- **Not in scope:** turning a message into a task. That is the point of the
  whole idea and it is the first thing here that writes, so it gets its own
  change and its own evidence.
- **Also not in scope:** changing anything in the mailbox — no flags, no
  moving, no marking read — and nothing about how mail reaches the directory.
  Marking a message read and archiving it so it stops appearing is wanted and
  is the natural next step; it is the first thing here that would write to the
  mailbox, so it waits for its own change.

## Capabilities

### Modified Capabilities

- `task-board`: requirements added for reading a maildir's named folders, for
  grouping messages into threads, for mail appearing in the inbox, for what a
  row shows, for opening what a thread points at, and for the board still
  working when the mailbox cannot be read. One requirement modified — the
  inbox view, which today lists its tasks "and nothing else". The project
  keeps one capability, and the tracker's and calendar's requirements live in
  it already.

## Impact

- A new module for the mailbox, in the shape `tracker.py` and `ical.py`
  established: its own configuration, one failure type, plain records.
- `main.py` — a view, a row, and the refusals every foreign row already has.
- No new dependency. `mailbox`, `email` and `email.header` are all standard.
- The sample maildir used to design this is the same format as the real input,
  which is a property neither of the other two sources has: the calendar
  cannot be faked at all, and the tracker needs a network stub.
