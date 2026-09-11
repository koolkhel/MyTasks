## Why

Reviewing a mail row is the slowest thing the board does, and the cost is not
Exchange's. A measured review spends 81.9 seconds of 88.9 on opening folders —
92% — because the gateway the board talks IMAP to has to enumerate a folder
over EWS every time a folder is selected. The board asks for the right things;
the protocol in between makes each question expensive.

Asked directly, the same questions are cheap. Measured against the same
account, with the same credential:

| what the board does on a review | through the gateway | asked directly |
| --- | --- | --- |
| search a source folder for 8 identities | ~1.1s | 0.42s |
| open the archive | 6.9–16.6s | there is no such request |
| count the archive (20,821 items) | — | 0.00s, it is metadata |
| search the archive for 8 identities | an open, then ~1.1s | 0.96s |
| move a message | part of the 88.9s | 0.18s |
| mark a message read | part of the 88.9s | 0.10s |
| authenticate | 0.58s | 1.79s cold, 0.00s warm |

A folder open — the thing that dominates a review — has no counterpart when
the account is asked directly: a search costs about a second whether the
folder holds 33 items or 20,821, because nothing is opened to answer it.

## What Changes

- The board reviews, archives and restores mail by talking to the mail
  account directly over its own web service, rather than through a local
  gateway that translates IMAP.
- **The reading of mail does not change.** The board goes on reading the
  mirrored maildir that a sync tool fills. This was measured, not assumed: the
  mirror holds 1,252 messages in 919 threads and is read from disk in 0.87s,
  where the same set fetched over the web service costs 20–30s — 300 messages
  with bodies took 7.99s, and 600 identities alone took 10.03s. Reading stays
  where it is fast.
- What the board needs configured changes: the address of the account's web
  service, rather than the host and port of a local gateway. The credential is
  still fetched from the keychain at the moment it is needed.
- Two requirements that describe the cost of a review in the old protocol's
  terms are restated: one counts folder opens, the other quotes the seconds a
  row takes and says the cost is mostly opening the archive.
- The sync tool and the local gateway stay installed and go on filling the
  mirror. Nothing in this change removes them; it stops the board from
  needing the gateway for its own writes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `task-board`: *An archive is confirmed before a row is retired* counts folder
  opens in a scenario, and the count is of a request that no longer exists —
  restated as one confirmation per row. *The board shows whether the mailbox
  is busy* justifies itself with measured seconds and names opening the archive
  as the cost; the requirement stands and its reasoning is replaced. One
  requirement is added: how the account is reached is configured, which the
  board has always done and the spec has never said.

## Impact

- `gateway.py` (569 lines) keeps every public name — `Server`, `numbers`,
  `present`, `move`, `mark_seen`, `archive`, `restore`, both exceptions — and
  changes what they say underneath. `main.py` does not change.
- `mail.py` does not change. Neither does the maildir, the sync tool, or any
  requirement about reading.
- `tests/fakeimap.py` (183 lines) is replaced by a fake of the new
  conversation at the same seam: `Server(config, connect=...)` already exists
  for exactly this, so `tests/stub/t_gateway.py` (209 checks) keeps its shape.
- `tests/gateway/t_gwlive.py` (475 lines) is rewritten — it drives a real
  server and the protocol it drives changes.
- One new dependency, which brings 14 transitive ones, all as wheels on the
  Python this board runs. The board has four today.
