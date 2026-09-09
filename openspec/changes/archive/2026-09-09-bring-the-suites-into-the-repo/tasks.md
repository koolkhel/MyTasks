## 1. Record what the suites do now, before touching them

- [x] 1.1 Run every one of the 64 current suites in its scratchpad form and record each one's check lines and exit status to a file — the stubbed ones as a batch, the store and tracker ones paced — so the imported copies have something to be compared against; verify the record holds 64 entries and names which tier each was run in
- [x] 1.2 Confirm the tier of every suite by measurement rather than by its imports: run each candidate for the self-contained tier with the environment emptied and no `.env` reachable, and verify each gives the same result that way as it does with the environment present; a suite whose result changes has a hidden dependency and moves tier (`t_twins5` fails 2 of 14 checks either way, which is its known failure rather than a dependency)

## 2. Scrub the identifiers, before anything is staged

- [x] 2.1 Replace the real tracker key in the seven suites that carry it (`t_green2`, `t_green3`, `t_label2`, `t_star`, `t_top`, `t_track2`, `t_track3`) with an invented key of the same shape — uppercase letters, a dash, digits — and the other project's code in `t_top` likewise; verify each of those seven still passes with the same check lines as its record from 1.1
- [x] 2.2 Verify the replacement key is still recognised for the right reason: break the recognition deliberately and confirm the affected checks fail, so the suite is not passing because it stopped testing anything
- [x] 2.3 Keep the account's real tag title rather than inventing one: it is a colour word, not the class of identifier the privacy requirement names, and one live suite asserts it because it is what the account actually returns — verify it is a tag title only, appearing in the harness default and two stub suites beside that live one, and that no other account data travels with it
- [x] 2.3a Record, beside the known failures, that one shipped check does not isolate what its name claims: `t_mailview`'s "a thread naming a configured issue opens the issue" passes with key recognition removed entirely, because the fixture body carries the literal issue URL as well as the key — `t_keys2` is what actually covers recognition; verify the note names both suites
- [x] 2.4 Grep the whole set of files about to be imported for the scrubbed key, the other project code, addresses and credentials, and verify there are no matches

## 3. Layout and shared support

- [x] 3.1 Create `tests/` with one directory per tier, and move the self-contained suites into the self-contained one; verify the directory holds 38 files — 39 less the one excluded for needing a snapshot of the old product — and that `ls` alone tells a reader what each tier needs
- [x] 3.1a Put the files that assert nothing under a probes directory of their own, and verify each contains no check idiom at all — the test for a probe is that it cannot fail, not that it printed no checks; two of the four (`t_keys`, `t_tension`) were lost from the scratchpad before they could be imported, leaving `t_cyr` and `t_cyr2`
- [x] 3.2 Move the shared harness and the baseline loader beside the suites, and make every suite find the repository and its neighbours by a path derived from its own location; verify no file under `tests/` contains an absolute path by grepping for the scratchpad and repository prefixes
- [x] 3.3 Verify the checkout can be anywhere: copy the repository to a second path, run the self-contained tier there, and confirm it passes with the same counts

- [x] 3.3a Separate the suites that read the board's own configuration into a tier of their own, and verify on a checkout with no `.env` that the self-contained tier passes entire — an emptied environment does not settle this, because configuration is found relative to the module that asks for it

## 4. The fixture

- [x] 4.1 Move the synthetic sample maildir under `tests/` as a fixture and commit the generator that produced it alongside; verify re-running the generator produces a mailbox with the same properties — same message count, the same one already marked read, the same unparseable one
- [x] 4.2 Make every suite that exercises mailbox writing copy the fixture per run rather than reading it in place, through one shared helper so the three suites cannot disagree; verify each of the five mail suites passes against its 1.1 record
- [x] 4.3 Verify the committed fixture is untouched by a whole run: record a digest of every fixture file, run the self-contained tier, and confirm the digest is identical afterwards

## 5. The runner

- [x] 5.1 Write the runner so it discovers suites by tier directory and never imports one to classify it; verify it lists 34, 4, 18 and 3 suites for the four tiers without opening a network connection, by running discovery with the environment emptied
- [x] 5.1a Verify the runner never runs or counts a probe: run every tier and confirm no probe appears in the counts or the summary
- [x] 5.2 Make a run with nothing asked for execute the self-contained tier only; verify on a copy of the repository with no `.env` present that it runs 34 suites, skips none for want of credentials, and exits zero
- [x] 5.3 Make the store and tracker tiers run only when asked for explicitly, and refuse to start when the credentials that tier needs are absent — naming which are missing; verify on a checkout with no `.env` at all, since emptying the environment does not remove the file the credentials actually live in, and confirm nothing ran and nothing failed
- [x] 5.4 Report a summary: the tier that ran, suites passed and failed, known failures, and the throttle count; verify the summary against a deliberately failing suite that the run identifies well enough to be re-run alone
- [x] 5.5 Verify the runner surfaces a suite's own check lines on failure rather than only its exit status, by making one check fail and confirming the failing check's text reaches the summary

## 6. Known failures

- [x] 6.1 Record the seven currently failing suites as known failures with a one-line reason each — `t_twins5` and `t_top6` naming the checks that fail, `t_label6` that it reads live tracker issues, and `t_place`, `t_perf`, `t_undo6`, `t_work6` that they crash where a created task is not found on the board and are not diagnosed
- [x] 6.2 Verify a known failure does not fail the run: run the self-contained tier and confirm it exits zero with `t_twins5` reported as known
- [x] 6.3 Verify a known failure that starts passing is reported: add a passing suite to the list temporarily, confirm the run says so, then remove it
- [x] 6.4 Verify a known failure that fails differently is not absorbed: make a listed suite fail an additional check and confirm the run reports it rather than counting it as known

## 7. The store tier

- [x] 7.1 Move the 18 store suites into their tier and have the runner execute them one at a time with a gap between them; verify against the live account that a run of the whole tier completes without a throttle error, and that each suite's check lines match its 1.1 record
- [x] 7.2 Count throttle errors and report a throttled run as inconclusive rather than as failures; verify by simulating the store's throttle response so the run reports the count and says the result is inconclusive, without needing to exhaust the real quota
- [x] 7.3 Verify the store tier leaves nothing behind: run it against the live account, then query the account for anything named as a test's and confirm there is none
- [x] 7.4 Have the runner report what a store run left behind rather than leaving it to be noticed; verify by creating a task named as a test's before a run and confirming the run reports it

- [x] 7.5 Launch every store-tier suite with the account's second token, read from `SINGULARITY_TEST_TOKEN` in the gitignored `.env` and passed as the suite's `SINGULARITY_TOKEN`; verify a launched suite reports a token ending in the test token's last four characters and that no product file mentions a test token
- [x] 7.6 Verify a checkout with only one token still works: unset the test token and confirm a store-tier run proceeds with the ordinary one rather than refusing
- [x] 7.7 Verify the run names which token it used without printing it, and that the token appears in no file the repository tracks

## 8. The tracker tier

- [x] 8.1 Move the three tracker suites into their tier; verify against the live tracker that each produces the same check lines as its 1.1 record, and that asking for this tier without the tracker configured refuses to start rather than failing every check

## 9. Keeping the account out of the repository

- [x] 9.1 Have the capture script write baselines and captured views to a directory the repository excludes, and add that directory to `.gitignore`; verify `git status` is clean after a run that records a baseline
- [x] 9.2 Verify the four baseline-reading suites still refuse a baseline that is absent or from another day, by running one with the baseline removed and again with its recorded day altered, and confirming each exits with instructions rather than comparing

## 10. The commit convention

- [x] 10.1 Amend the archive guidance in `openspec/config.yaml` so the staging pathspec includes `tests`, and verify the CLI reads the amended guidance back with the entry count unchanged apart from that edit
- [x] 10.2 Verify the amendment is what it claims: stage the change with the documented pathspec and confirm the fixture files appear in `git diff --cached --name-only`

## 12. The five suites lost mid-change

- [x] 12.1 Rewrite `t_add` (stub) from its 18 recorded checks: the row present before the store answers, the typed title, the counts, the selection, the placeholder id traded for the server's, a write queued behind a creation reaching the real id, and a refused creation removing the row and being reported — verify it reports 18 checks whose names match the record
- [x] 12.2 Rewrite `t_add2` (store) from its 13 recorded checks: a created task's stored order past everything the day holds, existing orders unmoved, successive additions distinct and ordered, a task added to an empty day carrying the board's chosen order rather than zero, and one added to the inbox carrying the API's default — verify 13 checks matching the record and that it deletes what it creates
- [x] 12.3 Rewrite `t_live` (store) from its 21 recorded checks: tick, untick, cancel, rename, date assignment and deletion each shown before the store answers and then agreed by the store, a refused done-for-today record not reported as failure, and a creation adopting the server's id — verify 21 checks matching the record and nothing left on the probe day
- [x] 12.4 Rewrite `t_live2` (store) from its 9 recorded checks: a task walked to the top and another to the bottom, the sequence surviving a reload and a return to the day, a fresh fetch agreeing, sorting by stored order alone agreeing, and every stored order distinct — verify 9 checks matching the record
- [x] 12.5 Rewrite `t_perf2` (store) from its 4 recorded checks: a tick costing no more than cursor movement, no tick near the old blocking latency, the board responsive with writes in flight, and every tick landing — verify 4 checks matching the record
- [x] 12.6 Record in the repo that these five are newly written and cannot be compared against the originals, unlike every other imported suite; verify the note names all five and says why the comparison is impossible


## 11. Verification

- [x] 11.1 Compare every imported suite against its 1.1 record, check line by check line, and verify each reports the same checks with the same outcomes — any difference is a mechanical edit that changed a measurement and must be explained or reverted; the self-contained tier is done (30 of 37 byte-identical, 7 explained: two non-deterministic orderings, two time-dependent, two reading real configuration, one key truncated mid-word)
- [x] 11.1a Re-record the four baseline-reading suites immediately before the comparison, against a baseline captured the same day, so that before and after see the same account state — their 1.1 records were taken on a different day and cannot otherwise be reproduced
- [x] 11.2 Verify a fresh clone works: clone the repository to a new path with no `.env`, install the requirements, run with nothing asked for, and confirm 34 suites run and the run exits zero
- [x] 11.3 Verify no regression to the board: it should be untouched, so confirm `git diff` names no file outside `tests/`, `.gitignore` and `openspec/`, and that the board still starts and shows today
- [x] 11.4 Grep the whole tracked tree, not only the staged diff, for the scrubbed tracker key and the other project code, and verify there are no matches
