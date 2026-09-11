## Context

See proposal.md - Why. The requirements are in `specs/task-board/spec.md`;
this explains how they are met.

What exists today, read from the source rather than assumed:

- `tracker.ISSUE_FIELDS` asks for `customFields(name,value(name,localizedName,login))`
  -- every custom field of every issue, not a named subset. The version is
  already on the wire.
- `tracker._custom_fields` keeps a field only when its value is a `dict`, so
  every multi-value field is discarded before anything sees it.
- A tracker row is a `Task` carrying the issue's facts under private raw keys
  (`_tracker_url`, `_tracker_state`, and so on) and the work project's id, so
  the existing keys hide it, count it and open it with no special case.
- `action_open_link` routes through a method of the app's own rather than the
  standard library, *"so a test can intercept it and assert the address
  without launching a browser -- which is what makes this, rather than the
  clickable span, the path that ships verified."* The same reasoning applies
  to starting a program, more strongly.
- `gateway.py` already runs a program: `subprocess.run(list(...))`, a list,
  no shell. That is the precedent to follow.
- `LinkPicker(title, choices)` is a modal over `(shown, value)` pairs that
  dismisses with the value. It is already the board's answer to "several
  things, pick one".

A probe against the configured tracker (field names only) found:

```
  Fix versions          list[0] or list[1]    dropped today
  Affected versions     list[2]               dropped today
  Component             single                kept
  Subsystems            list                  dropped today
```

Two facts follow. Both candidate version fields are lists, so keeping only
single values would keep neither. And issues with no version exist right now,
so that case is live rather than hypothetical.

## Goals / Non-Goals

Goals:

- The board hands three facts to one configured program and gets out of the
  way.
- Nothing the board displays can influence what is run.
- The command line is assertable in the self-contained tier without running
  anything.

Non-Goals:

- The program. It lives outside this repository. This change fixes only its
  command line.
- Any knowledge of git, ssh, a terminal emulator, a host, a branch or a
  directory inside the board.
- Waiting for the program, reporting its progress, or knowing whether it
  succeeded.
- Reviving every dropped custom field. Only values that are a mapping or a
  list of mappings are kept; a bare number, such as a due date, stays
  dropped as it is today.

## Decisions

### The board runs a program; it does not compose one

The configured value is a path to an executable, and the board builds an
argument list for it. It is not a template with placeholders, and it is not a
command line.

A template invites `work-on {key} --version {version}`, which invites
expanding it, which invites a shell, which makes a version name the tracker
holds into a question about this board's safety. A path plus a list of
arguments has no such step in it.

This is the same line the board already draws for addresses: *"Only web
addresses are opened"* exists because a title, a note and an event's location
are text the board did not author. An issue's field values are text the board
did not author either.

Alternative considered: a shell snippet in the configuration, which would let
the whole thing live in `.env` with no second file. Rejected on the above, and
because a snippet in a dotenv value cannot be run by hand, which is where a
checkout script is actually debugged.

### Three arguments, named

```
    <program> --key PROJ-1234 --project PROJ --version 1.6-1
```

Named rather than positional, so a fourth can be added later without breaking
a script written against three.

A **version** goes over, never a branch and never a directory. The two are
different transforms of the same version and the board should express neither:
a version of `1.6-1` can mean a branch `release/1.6-1` and a directory
`RELEASE-1.6-1` at the same time, and a board that sent one of them would be
holding half the program's naming convention.

Three because they are exactly what the board holds and the program does not.
Every single-valued custom field is already arriving, so `Component` or `Type`
would cost no request -- but each is a requirement to write down and a promise
to keep, so they are added on evidence rather than in advance.

### The version field is named in the configuration

`Fix versions` and `Affected versions` mean different things -- where it will
be fixed, where it was found -- and which one names the branch to check out is
a convention, not a fact about trackers. The board already takes the tracker's
vocabulary from the environment (`YOUTRACK_STATES`, `YOUTRACK_PROJECTS`); the
version field joins them.

### Keeping multi-value fields

`_custom_fields` grows a branch for a list of mappings, keeping their names in
order. Every field the tracker returns is already in hand, so this is a parser
change and no request changes -- which is also what makes "reading it costs no
further request" a requirement that can be checked by counting requests.

The narrow scope is deliberate: a mapping, or a list of mappings. A bare
scalar value stays dropped. Widening it further would change what other fields
mean for no present need.

### The version is always asked, and the issue proposes the answer

`TaskInput(prompt, value)` -- the one-line prompt the board already uses -- with
the issue's version filled in. The date key already does exactly this, opening
prefilled with today, and for the same reason: the board knows the likely
answer and the person knows the actual one.

Not `LinkPicker`. A picker offers the versions the issue names and nothing
else, and the version an issue is recorded against is where a problem was
found or is due -- not necessarily the version somebody is about to work in. A
prompt lets a person type a version the issue never mentioned, which a picker
cannot.

Where an issue names several, the first is proposed. Offering all of them
would be a picker again, and having chosen one a person would still want to
edit it.

**A consequence worth stating: a workspace can no longer be started without a
version.** `TaskInput` dismisses with nothing when the text is empty, so an
emptied prompt cancels -- which is how `Rename` and `Add` already behave, and
making this one key behave differently would be worse than the restriction.
So `--version` is always present, and the "no version" path disappears from
the command line entirely.

Alternative considered: a prompt whose empty answer means "no version", by
distinguishing an empty submission from an escape. Rejected -- it would make
this the only prompt on the board where clearing the field does something
rather than nothing.

### Started, not awaited

`subprocess.Popen`, not `run`. The board does not block, and it never learns
the program's exit code -- what happens next is visible where the program puts
it, which is the whole point of a program that opens a terminal.

Popen raises immediately when the program cannot be executed, which is exactly
the "could not be started" signal the requirement asks for, and nothing else
has to be inspected to produce it.

### The key is `W`

Free in both layouts (`keys("W")` gives `W,Ц`, neither bound), and next to `w`
for hiding work: the same subject, a different act.

### Routed through a method of the app's own

One method takes the argument list and starts it. A suite replaces that method
and asserts the list, exactly as the link suites replace the opener and assert
the address. Nothing in the self-contained tier ever starts a process.

A suite also greps the source for `shell=True` and for string formatting
reaching the launch, because the safety property is about what the code cannot
do rather than about what one run did.

## The program's own shape, for reference

Not part of this change -- it lives outside this repository -- but the command
line only makes sense against a sketch of what reads it. Placeholders
throughout; the real names belong in the script, not here.

```bash
#!/usr/bin/env bash
# work-on --key PROJ-1234 --project PROJ --version 1.6-1
set -euo pipefail

KEY= PROJECT= VERSION=
while [[ $# -gt 0 ]]; do
  case "$1" in
    --key)     KEY=$2;     shift 2 ;;
    --project) PROJECT=$2; shift 2 ;;
    --version) VERSION=$2; shift 2 ;;
    *) echo "work-on: unknown argument $1" >&2; exit 2 ;;
  esac
done

# The remote half is a script on the remote, called with arguments -- not a
# command line built here and quoted through ssh.  Building one means every
# value crossing two shells, and the board deliberately hands over values it
# has not sanitised because it should not have to.
kitten @ launch --type=tab --title "$KEY" \
    ssh -t <host> workspace "$PROJECT" "$VERSION" "$KEY"
```

and on the remote, `workspace`:

```bash
#!/usr/bin/env bash
set -euo pipefail
PROJECT=$1 VERSION=$2 KEY=$3

# A version becomes two different names, which is why the board sends
# neither: a directory, and a branch.
case "$PROJECT" in
  PROJ)
    ROOT=/data/<org>/<project>
    RELEASE="release/$VERSION"
    # url, the directory to put it in, the branch to check out.  The same
    # repository appears twice under different names at different branches,
    # so a list of repositories with one shared branch would not express it.
    CHECKOUTS=(
        "<gitlab>/<group>/proj|proj|$RELEASE"
        "<gitlab>/<group>/proj-builder|proj-builder|$RELEASE"
        "<gitlab>/<group>/proj|proj-jenkins|proj/develop"
    )
    ;;
  *) echo "no workspace configured for $PROJECT" >&2; exit 2 ;;
esac

DIR="$ROOT/RELEASE-$VERSION/$KEY"
mkdir -p "$DIR" && cd "$DIR"
for entry in "${CHECKOUTS[@]}"; do
    IFS="|" read -r url dir branch <<< "$entry"
    [[ -d $dir ]] || git clone --recursive -b "$branch" "$url.git" "$dir"
done
exec claude
```

Two things this shape had to accommodate, both found by writing a real one
out: the same repository is checked out twice under different names at
different branches, so a list of repositories sharing one branch would not
express it; and the directory name and the branch name are different
transforms of the version, which is why the board sends the version and
neither of the two.

Everything that changes often is in these two files. Nothing in them is
described by the spec except the first line of the first one.

## Risks / Trade-offs

- **A program that fails after starting is invisible to the board.** By
  design: it fails in the tab it opened, which is where a person is looking.
  The board's honest report is "started" or "could not start", and pretending
  to more would be a lie about a process it does not own.
- **Whoever can write `.env` can make the board run anything.** True, and the
  same file already holds the token that can rewrite the task store and the
  command that yields the mail password. This adds no new trust boundary --
  but it does mean the configured value must be a path the board execs, never
  a string it interprets, which is the decision above.
- **A tracker whose version field is renamed silently stops providing one.**
  Issues then have no version and the program is told none, which is the same
  as an issue that genuinely has none. The board cannot tell them apart.
  Naming a field that does not exist is not distinguishable from a field no
  issue fills in, and inventing a complaint would fire on the ordinary case.
- **The remote side has to be reachable and kitty's remote control enabled.**
  Neither is the board's business, and both fail visibly the first time.

## Migration Plan

None. With no program configured the key says so and nothing else changes;
with no version field configured the tracker rows are exactly what they are
today. Removing either line from `.env` puts the board back.

## Open Questions

None that change the specs, the approach or the tasks. Which fields a future
script wants beyond three is a question the script will answer by needing one.
