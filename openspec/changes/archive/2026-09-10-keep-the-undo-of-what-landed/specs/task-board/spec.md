## MODIFIED Requirements

### Requirement: Undoing reaches back, and never turns round

An undo SHALL NOT itself become something to undo: pressing the key again SHALL reach further back rather than reinstating what was just reversed.

A write the API refused SHALL NOT be reachable, because it never took effect.

An action of which any write landed SHALL remain reachable, however many of
its other writes were refused. An action is one thing a person did and one
entry on the stack, while it may take several writes — moving a task respaces
its run, one write a task — and a refusal among them does not unhappen the
rest. Throwing the entry away would take with it the ability to undo work the
board is still showing.

Whether an entry is dropped SHALL NOT depend on the order in which an action's
writes settle. The question the board has to answer — did this action leave
anything behind? — is unanswerable while any of its writes is still in flight,
so it SHALL be answered once they have all settled and not before. An entry
decided early is an entry decided by whichever answer the network happened to
return first.

#### Scenario: Pressing undo twice does not turn round

- **WHEN** a person undoes a write and presses the undo key again
- **THEN** the write before it is reversed, not the undo itself

#### Scenario: A refused write is not on the stack

- **WHEN** a write is refused and a person presses the undo key
- **THEN** the refused write is not reversed, because it never happened, and the key reaches past it to the last write that did

#### Scenario: An action that partly landed stays reachable

- **WHEN** an action takes several writes, one is refused and the others are accepted
- **THEN** the undo key reverses what the accepted writes did

#### Scenario: An action that landed nothing is not reachable

- **WHEN** every write an action took is refused
- **THEN** the action is not reversed, and the key reaches past it to the last write that did land

#### Scenario: The order the answers arrive in makes no difference

- **WHEN** the same action is performed twice, its refusal answered before its other writes on one occasion and after them on the other
- **THEN** the undo key reaches the same thing both times
