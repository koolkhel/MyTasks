## 1. Remembering what a write replaced

- [x] 1.1 Add an undo entry holding the label of the action, the task ids it wrote, and the previous values of the fields it changed for each of them, so one entry can span several tasks; verify a check that an entry built from two tasks reports both, and that its fields are only those the write changed
- [x] 1.2 Keep the entry when a write is confirmed rather than dropping it, pushing it onto a session-long stack, and confirm a refused write pushes nothing; verify a check that a confirmed write leaves one entry and a refused write leaves none
- [x] 1.3 Record the three writes that cannot be reversed — deleting, adding, and filing a task that had no project — as entries that name themselves but are never acted on; verify a check that each is on the stack, is marked as unreversible, and carries no previous values to send
- [x] 1.4 Make one action produce one entry however many requests it sent, so that a move which respaces its run is a single entry covering every task it wrote; verify a check on a run with no numbering room that the five writes it takes leave exactly one entry naming all four tasks
- [x] 1.5 Confirm the stack does not outlive the board; verify a check that a freshly constructed board has nothing to undo

## 2. Reversing a write

- [x] 2.1 Add the action that takes the most recent entry and sends its previous values back, through the same optimistic path as any other write; verify a check that reversing a recorded tick sends one update carrying only `checked`, with the value the task had before
- [x] 2.2 Confirm an undo restores only the fields its own write changed; verify a check that renaming a task, changing something else about it, then undoing the rename returns the title and leaves the other change alone
- [x] 2.3 Make an undo entry pop whether or not the write it sends succeeds, and take a refused undo back like any other refused write; verify with a stubbed client that fails the update that the view returns to what it showed, the refusal is reported, and the entry is not left to be retried
- [x] 2.4 Handle a task that no longer exists; verify with a stubbed client that returns a not-found error that the board says so and the entry is discarded rather than retried
- [x] 2.5 Confirm an undo is not itself pushed onto the stack; verify a check that undoing once then pressing again reverses the write before it, not the undo

## 3. What cannot be undone

- [x] 3.1 Report a deletion as unreversible, naming it, and create nothing; verify with `Pilot` that deleting a task then pressing the key says a deletion cannot be undone and that no task appears
- [x] 3.2 Report a first filing as unreversible, naming it, and leave the project in place; verify with `Pilot` that filing an unfiled task then pressing the key says so and the task keeps its project
- [x] 3.3 Report an addition as unreversible and point at deleting instead; verify with `Pilot` that adding a task then pressing the key says so and the task still exists
- [x] 3.4 Confirm the key never destroys anything; verify with `Pilot` that pressing it repeatedly after a mixture of writes deletes no task
- [x] 3.5 Confirm moving between projects is reversible, unlike a first filing; verify with `Pilot` that a task moved from one project to another returns to the first
- [x] 3.6 Confirm undo and confirmation cover the same set; verify a check that every action recorded as unreversible is one the board confirms beforehand, and that no confirmed action is recorded as reversible

## 4. Done for today

- [x] 4.1 Restore the date a task was moved from, and report that the record of the day's work remains; verify with `Pilot` that undoing it puts the task back on its previous date and that the message says the record could not be withdrawn
- [x] 4.2 Confirm the task returns to the view it came from; verify with `Pilot` that after the undo it appears in the day it was on, not the day it was moved to
- [x] 4.3 Confirm the board does not imply a full reversal; verify a check that the message names what was not undone

## 5. The key, and what it says

- [x] 5.1 Bind the key, with its key bar and help entries, and confirm the Russian twin comes from the existing table; verify with `Pilot` that both the English and the Russian character reach the action, and that the bar names only the English one
- [x] 5.2 Name what each undo reversed, including the task it acted on; verify with `Pilot` that the message after undoing a tick names both the action and the task
- [x] 5.3 Say when there is nothing left; verify with `Pilot` that pressing the key with an empty stack says so and changes nothing
- [x] 5.4 Confirm the key needs no task selected and works whichever view is shown; verify with `Pilot` that a write made on one day is undone after navigating to another, and that the message names the task
- [x] 5.5 Confirm the key bar still shows every entry without clipping now that another has been added; verify a check that packing its entries at widths from 50 columns upward drops and repeats nothing

## 6. Verify against the live API

- [x] 6.1 Exercise undo end to end on a far-future day: create throwaway tasks, tick one and undo it, rename one and undo it, move one and undo it, then delete them; select by task id before each keypress and confirm each reversal by re-fetching the task and comparing the fields
- [x] 6.2 Confirm a move that respaces its run is reversed by one press; verify against the live API on four tasks holding adjacent stored orders that one move followed by one undo returns every one of them to the value it started with
- [x] 6.3 Confirm no regression: verify the previously passing suites still pass, and that today's view, the inbox and the someday view show the same tasks and counts as captures taken beforehand
