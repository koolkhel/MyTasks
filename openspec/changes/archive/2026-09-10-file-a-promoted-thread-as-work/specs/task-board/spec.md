## ADDED Requirements

### Requirement: A promoted task is filed as work

The task a promotion makes SHALL belong to the work project, so that the key
which hides work hides it as it hides any other work task. Promoting is the
one action in which a person declares that a message is work; the task it
makes SHALL be work by the board's own reckoning, and not the single task that
cannot be treated as such.

Nothing further SHALL be said about counting or hiding it. A promoted task is
a task, so every undertaking the board already gives about a task in the work
project — that hiding removes it, that the report of what was hidden includes
it, that showing work brings it back — holds for it by that fact alone. The
requirements that say a tracker issue or a work account's event counts as work
exist because those rows are not tasks and have no project to be read.

It SHALL be filed under whichever project counts as work, and the board SHALL
NOT name a project of its own for this. Where no work project is configured,
promoting SHALL still make the task, unfiled, and SHALL report nothing beyond
what a promotion already reports: the key that hides work is where a missing
setting is answered, and it answers there already.

The task SHALL be filed from the moment it exists, rather than made and then
filed. Two things follow, and both are the reason: there is no moment at which
a promoted task is on the board unfiled, and a promotion is never a first
filing of a task that already exists — so the confirmation the board asks
before filing such a task is not owed here. That confirmation guards a change
that cannot be reversed; undoing a promotion removes the task altogether,
which leaves nothing filed to regret.

Everything else a promotion promises SHALL be unaffected: the title taken from
the thread, the day it lands on, the message it carries, its appearance before
the store has answered, and its removal by undo.

#### Scenario: The promoted task is hidden with the rest of the work

- **WHEN** a thread has been promoted and work is hidden on the day the task landed
- **THEN** the task is hidden with the other work tasks, and showing work brings it back

#### Scenario: It is filed in the request that creates it

- **WHEN** a thread is promoted
- **THEN** the task is created belonging to the work project, with no separate filing of it afterwards

#### Scenario: Promoting asks nothing

- **WHEN** a person promotes a thread
- **THEN** the task is made and filed with no confirmation asked, because no existing task is being filed

#### Scenario: Promoting with no work project configured

- **WHEN** no work project is configured and a thread is promoted
- **THEN** the task is created with no project, and the board says nothing it would not have said anyway

#### Scenario: The task is otherwise what it was

- **WHEN** a thread is promoted
- **THEN** it is titled from the thread, lands on today, carries the message it came from, and is shown before the store has answered

#### Scenario: Undoing a promotion leaves nothing filed

- **WHEN** a person promotes a thread and then undoes it
- **THEN** the task is removed, so no task remains filed under the work project by that promotion
