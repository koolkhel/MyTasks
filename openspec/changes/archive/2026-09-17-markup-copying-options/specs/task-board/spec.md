## MODIFIED Requirements

### Requirement: Copying the marked rows as text

The board SHALL offer two keys that put the marked rows on the system
clipboard, one line for each row, so that they can be pasted into any editor.
They differ only in what a line says.

The first SHALL write each row as **plain text**: the row's title and nothing
else. An editor that adds its own bullet to every line would otherwise be
given a second one, and a line that arrives as `- - [ ] write it up` has to be
cleaned up by hand.

The second SHALL write each row as **markdown**. An unfinished task SHALL be
written with an empty box, a finished one with a ticked box, and a cancelled
one with a ticked box and its title struck through. Cancelled is a third state
and markdown has two boxes; striking the title is what keeps it from being
read back as an ordinary finished task. A row the board does not own carries
no tick state of its own and SHALL be written as unfinished.

The plain form therefore says nothing about whether a row is finished, and a
set copied plainly and pasted back SHALL arrive as unfinished tasks. That is
what plain means here rather than an oversight: there is no way to say
"finished" in a line with no markup in it without inventing a marker, and the
board's rule for copying and pasting is that it is as simple as a notepad.
Where the tick state matters, the markdown form is the one that carries it.

Everything else SHALL be the same for both keys.

The title SHALL be written as the row carries it rather than as the column
drew it: before it was shortened to fit, and before a count of messages was
appended to a mail subject.

The lines SHALL be in the order the rows were marked. Marks may be gathered
from views that share no ordering, so the order of marking is the only one
that is defined wherever the rows came from.

Every marked row SHALL be copied, including one a search or the work filter is
hiding at the time. A mark is on a row rather than on a drawn line, and the
board says how many rows are marked, so a row copied while hidden is not a row
copied in secret.

The board SHALL say what it copied, and SHALL say which of the two forms it
wrote. The two keys are one keypress apart and what they produce differs only
once it has been pasted somewhere else; a board that reported both the same
way would let a person discover the mistake in the other application.

Pressing either key with nothing marked SHALL say so and SHALL leave the
clipboard alone, rather than replacing whatever the person had with nothing.

#### Scenario: The three states of a task

- **WHEN** an unfinished task, a finished task and a cancelled task are marked and copied as markdown
- **THEN** the unfinished one carries an empty box, the finished one a ticked box, and the cancelled one a ticked box with its title struck through

#### Scenario: A row from a source copies as unfinished

- **WHEN** a mail row, a calendar event or a tracker issue is marked and copied as markdown
- **THEN** its line carries the row's title and an empty box, because such a row has no tick state of its own

#### Scenario: The title is the one the row carries

- **WHEN** a row whose title the column shortened, or a mail row drawn with a count of messages beside its subject, is marked and copied
- **THEN** the copied line carries the whole title without the shortening and without the count, whichever form was copied

#### Scenario: The order is the order of marking

- **WHEN** rows are marked in one order and copied
- **THEN** the lines are in the order the rows were marked, whatever order the views drew them in, whichever form was copied

#### Scenario: A marked row a filter is hiding

- **WHEN** a row is marked and a search or the work filter then hides it, and the person copies
- **THEN** that row is copied with the rest, and the count of marked rows had said it was there

#### Scenario: Copying with nothing marked

- **WHEN** a person presses either copying key with no row marked
- **THEN** the board says nothing is marked, and whatever was on the clipboard is still there

#### Scenario: The plain form is the title alone

- **WHEN** rows are marked and copied plainly
- **THEN** each line is the row's title with no bullet, no box and no striking, and an editor that adds a bullet of its own produces one bullet rather than two

#### Scenario: The plain form does not carry finishedness

- **WHEN** a finished task and an unfinished one are marked and copied plainly
- **THEN** the two lines differ only in their titles, and pasting them back adds two unfinished tasks

#### Scenario: The markdown form still round-trips

- **WHEN** a finished task is copied as markdown and the line is pasted back
- **THEN** the task that arrives is finished

#### Scenario: The board says which form it copied

- **WHEN** rows are copied
- **THEN** the board reports how many rows it copied and which of the two forms it wrote, so that pressing the wrong key is visible before the paste

#### Scenario: Both keys are named where the keys are named

- **WHEN** a person looks at the key bar or the help screen
- **THEN** both copying keys are named, each said to be the plain one or the markdown one
