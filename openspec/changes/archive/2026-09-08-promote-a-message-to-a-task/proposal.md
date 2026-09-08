## Why

Reading mail on the board is worth little on its own — it is one more place to
look. The point is the decision: this message is work, so it becomes a task;
and then it leaves the queue.

Both halves matter. A promote that leaves the message in the inbox means the
queue never shrinks, and the inbox is where mail now lives — the view worked
through daily. A message already turned into a task, still sitting among the
things awaiting a decision, is precisely the friction the queue exists to
remove.

It also explains what a mail row *is*, which nothing else about the board
could: a candidate task awaiting a decision.

## What Changes

- A key turns the selected mail thread into a task on today, titled from what
  the thread is about.
- The task carries the message itself in its note — what the thread said, plus
  the identity of the message it came from. Measured on the sample: every
  thread's address appears inside its own body, so the note carries what the
  key that opens a link needs, *and* keeps the message a person had just read
  rather than replacing it with a bare address.
- Promoting marks the thread's messages read, which is a rename of a file in
  the maildir and nothing more. The board reads unread messages, so the row
  leaves the queue by the same rule that put it there.
- **This gives up a property worth naming**: until now the board altered
  nothing in the mailbox. That was clean, and it is being spent deliberately —
  a queue that cannot be drained from the board is a queue that will be
  drained somewhere else, which is one more place to look.
- Whatever syncs the maildir carries the flag to the server. The board writes
  a local file and knows nothing about any server, exactly as before.
- The write goes the way every write on this board goes: shown at once,
  queued behind the network, undoable, and reported if it fails.
- **Not in scope:** dismissing a message that is *not* work. Most notification
  mail is noise, so a queue with only a promote action still will not drain —
  but that is a second action with its own decisions, and it is called out in
  the design rather than smuggled in here.
- **Also not in scope:** moving a message to another folder, deleting
  anything, promoting into any view but today, or promoting more than one
  thread at once.

## Capabilities

### Modified Capabilities

- `task-board`: requirements added for turning a mail thread into a task, for
  what the created task carries, and for the message being marked read so the
  queue drains. Two modified — the list of actions the board offers gains
  promoting, and the requirement that the board alters nothing in the mailbox,
  which this change contradicts on purpose and must therefore restate.

## Impact

- `mail.py` — marking a message read, and reading unread messages only.
- `main.py` — a key, the task it creates, and the note it writes.
- The task store — one created task per promotion, through the call the board
  already uses to add a task.
- The mailbox — one file renamed per message promoted. Nothing moved, nothing
  deleted, no content touched.
