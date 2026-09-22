## Context

See proposal.md — Why. The constraints that shape the approach:

- `ical.Config` holds one work name and a tuple of personal names; `Config.accounts`
  is their union and `Config.is_work` takes a single account string.
- `ical.fetch` selects a calendar by comparing the title of its **source** against
  those names, collects every source title it saw, and raises `CalendarUnreadable`
  when a configured name is not among them — before returning anything.
- `main.py` routes that exception to a handler that sets `self.events = []` and
  records a standing message. The message survives refreshes and comes down when
  the source recovers; this is shared with the tracker, mail and the working
  window.
- `board.py` builds an event row from an `ical.Event`, calls
  `config.is_work(event.account)` to decide whether the row belongs to the work
  project, and builds the row id from the account, the start label and the title.

## Goals / Non-Goals

**Goals:**

- One configured name can select a single calendar, without a second variable or
  a new syntax.
- A name that matches nothing costs the person that one name, not the calendar.
- The work filter keeps working when what is configured as work names a calendar.

**Non-Goals:**

- Any notion of an event appearing before the day it falls on.
- Selecting a calendar by anything other than its title — no identifier, no
  source-qualified path, no pattern.
- Changing how a day is fetched, ordered, drawn or refused writes.

## Decisions

### An entry matches a source title or a calendar title, and a name matching both reads both

Alternatives considered: a qualified form (`<source>::<calendar>`), and a second
pair of variables for calendar-level names.

The either-match rule is chosen because it is what a person already expects — the
attempt that prompted this change was exactly this, typed into the existing
variable — and because the calendar title is the name the board already puts on
screen, in the column where a task shows its project. A configuration that cannot
accept the name the board itself displays is the surprise worth removing.

The qualified form was rejected for requiring the source title to be discovered
first, which is the thing nobody knows, and for introducing a separator that must
never occur in a real name. A second pair of variables was rejected for
duplicating the work/personal split across four entries.

Where one name is both a source title and some other calendar's title, both are
read. A union needs no precedence rule, and it is the only answer that never
silently drops something a person named.

### A calendar matched twice is read once

An account and one of its own calendars can both be named. The selection is
therefore deduplicated on the calendar's identifier before events are asked for;
without that the same calendar is fetched twice and every one of its events
appears as two rows.

### The selection rule is a pure function, separate from the framework

Choosing which calendars to read becomes a function from the configuration and a
sequence of `(source title, calendar title, identifier)` to the identifiers
chosen and the configured names that matched nothing. `fetch` gathers those
triples from the framework, calls it, and asks for events with the result.

This is what makes the rule testable at all. The self-contained tier must pass on
a fresh clone with nothing configured and no calendar framework present, and
today every route into `fetch` goes through `_store()` and the system's
permission — which is why the one existing check of the missing-name behaviour
lives in the tier that needs a real machine, and skips itself when the grant is
absent. A rule with no framework in it can be exercised in full where it will
actually be run.

### Names are normalised before they are compared

Both sides are normalised to NFC and then case-folded. The existing comparison
case-folds only. macOS hands back strings that may be decomposed, and a title
typed into the configuration composed will not equal a decomposed one however it
is cased — which fails in exactly the way this change exists to prevent, and
fails invisibly for names outside ASCII, which is the case in hand.

### An event keeps reporting the source it came from

`Event.account` stays the source title even when the calendar was matched by its
own name; `Event.calendar` already carries the calendar. The alternative — filling
`account` with whichever name matched — would make the same calendar's events
report different accounts depending on how they were selected, and would move the
row id, which is built from the account.

### `is_work` is given both names

`Config.is_work(account)` becomes `is_work(account, calendar)`, matching the work
name against either. Its one product call site has both to hand: `board.py` holds
the account and the calendar on the row it is building.

Passing the `Event` instead was rejected because the caller works in rows rather
than events everywhere else, and would then be the only place reaching back into
the calendar's own types.

### A name that matches nothing stops being an exception

`CalendarUnreadable` keeps the four things it names: no framework, no permission,
permission to write only, and no accounts on the machine at all. A configured name
that matches nothing is none of these — it is a correctable name, and the calendar
is readable — so `fetch` returns what it read together with the names that matched
nothing, rather than raising.

The return becomes a small frozen result carrying the events and the unmatched
names, rather than a bare tuple, so that the two cannot be taken in the wrong
order and so the day handler reads as what it is.

### The report reuses the standing-message field

The unmatched names are reported through the same field the calendar's other
trouble already uses, so there is no second channel and the status line needs no
change. The only difference from today is that setting that message no longer
empties the events: the handler takes both at once and applies both.

## Risks / Trade-offs

- **A day is now shown that is knowingly incomplete.** → The report stands until
  the name matches or goes, rather than appearing once and clearing, so the
  incompleteness is stated for as long as it lasts. This is the trade the spec
  states explicitly.
- **The union rule can read more than intended** when a calendar somewhere shares
  a name with a configured account. → Stated in the spec and covered by a
  scenario; the alternative silently drops a named calendar, which is worse and
  harder to notice.
- **Normalisation could change which names match today.** → Only by making
  previously-failing comparisons succeed; an ASCII name is unaffected, and no
  currently-matching name can stop matching.
- **`is_work`'s signature changes.** → One product call site, plus suites that
  construct a `Config`. Both are in this repository and are changed with it.
- **Deduplication is easy to leave out** and its symptom — every event doubled —
  only appears when an account and one of its calendars are both named, which no
  current configuration does. → Covered by a stub suite case rather than left to
  be noticed.

## Migration Plan

None required. An entry naming an account behaves exactly as it does now, so
every existing configuration keeps its current meaning; the change only widens
what an entry may name. Rollback is a revert — no stored state, no file format,
nothing written.

## Open Questions

- **Answered while applying (2026-09-22): it yields events, and no further
  permission is needed.** The calendar in hand is not derived from the address
  book at all — it is an ordinary CalDAV calendar in a self-hosted source, with
  23 events in the coming year, readable under the calendar permission the
  board already asks for. The source it sits in holds two other calendars, one
  of them far busier, which is the case per-calendar selection exists for. The
  original question is kept below as it was asked.

- Whether the calendar this change was prompted by yields events at all. A
  birthday calendar derived from the address book can require a Contacts
  permission that the board has never asked for, separate from the calendar
  permission it does ask for. This does not change the specs, the approach or the
  task breakdown — the selection work is the same either way — but it decides
  whether the change delivers the outcome, so it is settled first in tasks.md.
  If a Contacts grant turns out to be needed, that is a separate change.
