## 1. The label

- [x] 1.1 Replace the rule in `_state_label` with the state's last word, lowercased, and verify each configured state renders as expected: `In progress` as `progress`, `In review` as `review`, `Requires improvement` as `improvement`
- [x] 1.2 Keep a state with no words at all rendering as an empty label rather than raising, and verify with an empty string and a string of only spaces
- [x] 1.3 Keep the trim, so a last word longer than the column is cut rather than allowed to overflow, and verify with a synthetic state whose last word exceeds the width
- [x] 1.4 Verify a state already lowercase and one capitalised produce labels that differ only in the word, not in case

## 2. The width

- [x] 2.1 Raise the width constant to eleven, which is what `improvement` needs, and verify `improvement` survives the trim intact
- [x] 2.2 Declare the `When` column with that same constant instead of a second literal, and verify by reading the source that the number appears once
- [x] 2.3 Verify the widest label the board's own tasks put in that column still fits, by rendering a task overdue enough to produce the longest form alongside a tracker row

## 3. What the change does not disturb

- [x] 3.1 Correct the docstring on the overdue label in `singularity.py`, which explains its bound by reference to a column that is no longer that width, and verify the bound it describes still matches what the function returns
- [x] 3.2 Verify the day's own tasks are unchanged: same rows, same order, same when-labels, with the tracker configured and with it unconfigured
- [x] 3.3 Verify the block still groups by the configured order of the states and is still counted as `N tracked`, neither of which this change touches

## 4. Two states that read alike

- [x] 4.1 Verify with two synthetic states ending in the same word that their labels coincide and their rows still appear in separate runs, in the configured order

## 5. Verification

- [x] 5.1 Write a suite covering the labelling rule against the configured states and against multi-word, capitalised, single-word and empty states, and verify it passes
- [x] 5.2 Verify against the live tracker that today's block reads as expected for every state currently reported, and that the column shows no cut label
- [x] 5.3 Confirm no regression: run the existing suites, updating only those that assert the old eight-cell or `In `-stripping behaviour, and verify today, the inbox and the someday view show the same tasks and counts as captures taken beforehand
