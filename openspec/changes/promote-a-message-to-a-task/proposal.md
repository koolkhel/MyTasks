## Why

Reading mail on the board is worth little on its own — it is one more place to
look. The point is the decision: this message is work, so it becomes a task;
that one is noise, so it goes.

Without that, the mail view is a feed with extra steps. With it, mail stops
being a thing to keep on top of and becomes a queue that drains into the day.

It also explains what a mail row *is*, which nothing else about the board
could: a candidate task awaiting a decision. The board already has a view for
things awaiting a decision — the inbox holds undated tasks needing one — so
mail is a queue standing before that one.

## What Changes

- A key turns the selected mail thread into a task on today, titled from what
  the thread is about.
- The new task carries what the thread pointed at: its address, and the
  identity of the message it came from, in the note. So the task can still be
  opened to the thing it is about, by the key that already does that, and the
  message it came from can still be found.
- The write goes the way every write on this board goes: shown at once,
  queued behind the network, undoable, and reported if it fails.
- Promoting SHALL NOT change the mailbox. The board still writes nothing
  there. The message stays where it is, and the queue drains the way it
  already does — by archiving in whatever mail client fills the directory,
  after which the message is simply no longer read.
- **Not in scope:** flagging, moving or marking a message read; anything that
  reaches the mail server. Deliberately: the board writing to the mailbox is a
  boundary worth crossing only once there is a reason, and this change is
  useful without it.
- **Also not in scope:** promoting into any view but today, and promoting more
  than one thread at once. Both are additions rather than parts of this.

## Capabilities

### Modified Capabilities

- `task-board`: requirements added for turning a mail thread into a task, for
  what the created task carries, and for what promoting does not do — to the
  mailbox or to the thread's row. One requirement modified: the list of
  actions the board offers gains promoting a mail thread.

## Impact

- `main.py` — a key, the task it creates, and the note it writes.
- The task store — one created task per promotion, through the call the board
  already uses to add a task.
- Nothing new is read and nothing new is configured. The mailbox module gains
  nothing: promotion is entirely a matter of what the board does with a thread
  it has already read.
- Depends on the mailbox being read at all, which is its own change and comes
  first.
