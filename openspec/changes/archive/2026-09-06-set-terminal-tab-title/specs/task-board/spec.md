## ADDED Requirements

### Requirement: The board names its terminal tab, and gives the name back

While the board is running, it SHALL ask the terminal to name the tab or
window it occupies, so that the tab holding the board can be found among
others without opening it.

The name SHALL be fixed rather than describing the day shown, the counts, or
the view. A name that changes as work is done is noise where a tab bar is
scanned rather than read, and a fixed name is what makes the tab findable.

When the board exits it SHALL restore the title the terminal had before,
rather than leaving its own name behind or blanking the title. The board is
opened and quit often, and a tab left permanently misnamed is worse than one
that was never named.

The title SHALL be restored however the board exits, including when it exits
by failing. A crash SHALL NOT be the reason a terminal keeps the wrong name.

The board SHALL write nothing when its output is not a terminal, so that a
run whose output is piped or redirected stays free of control sequences.

Where the terminal cannot restore a previous title, the board SHALL still name
the tab while it runs: naming that outlives the board is a smaller fault than
never naming it, and the shell's next prompt commonly replaces the title in
any case.

#### Scenario: The tab is named while the board runs

- **WHEN** the board is started in a terminal
- **THEN** the tab or window it occupies is named for the board

#### Scenario: The name does not change as work is done

- **WHEN** tasks are ticked, added, reordered, or the shown view is changed
- **THEN** the name stays exactly as it was

#### Scenario: Quitting gives the title back

- **WHEN** a person quits the board
- **THEN** the terminal shows the title it had before the board was started

#### Scenario: Failing gives the title back too

- **WHEN** the board exits because of an error rather than being quit
- **THEN** the title is still restored

#### Scenario: Output that is not a terminal

- **WHEN** the board's output is piped or redirected rather than shown in a terminal
- **THEN** nothing is written to name the tab, and the output carries no control sequences

#### Scenario: A terminal that cannot restore the previous title

- **WHEN** the terminal does not support putting a previous title back
- **THEN** the tab is still named while the board runs, and the board does not fail on account of it
