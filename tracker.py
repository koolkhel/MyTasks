"""Read-only access to the issue tracker.

Only what a person's own board needs: the issues assigned to them and
currently in progress.  Nothing here writes -- issues are worked in the
tracker's own interface, and the board shows them so a day can be looked at
in one place.

The query shape and field selection follow a working digest built against
this same tracker; its roster validation and per-member grouping are not
carried over, because that reports on a team and this reports on one person.

Everything identifying -- where the tracker is, who to ask about, which
projects, which states -- comes from the environment.  None of it is written
here.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Sequence

import requests
from dotenv import load_dotenv

#: Asked of every issue.  `customFields` carries the assignee, the state and
#: the priority, which is where the tracker keeps them rather than at the top
#: level.
#:
#: `localizedName` is the tracker's own word for a value, which is what the
#: board shows a priority by.  One extra token on a request that already asks
#: for every custom field, so it costs no call and no page: the priority was
#: arriving all along and being thrown away for want of the word.
ISSUE_FIELDS = (
    "idReadable,summary,project(shortName),updated,"
    "customFields(name,value(name,localizedName,login))"
)
TIMEOUT_SECONDS = 15
#: Issues are read one page at a time; far more than a person has in progress.
MAX_ISSUES = 200


class TrackerUnreachable(Exception):
    """The tracker could not be reached or would not answer.

    Its own type so a caller can tell "the tracker is down" from "the board
    could not load the day": the two must never be reported as each other.
    """


@dataclass(frozen=True)
class Config:
    """Where the tracker is and which issues to ask for."""

    base_url: str
    token: str
    assignee: str
    projects: tuple[str, ...]
    #: The states whose issues are shown, in the order they should appear.
    #: Their order is the block's order, so whoever configures them has
    #: already said which matters most by writing it first.
    states: tuple[str, ...]

    @property
    def query(self) -> str:
        """The single query that selects the issues to show."""
        wanted = ", ".join(f"{{{state}}}" for state in self.states)
        parts = [f"Assignee: {self.assignee}", f"State: {wanted}"]
        if self.projects:
            parts.append(f"project: {', '.join(self.projects)}")
        return " ".join(parts)

    def issue_url(self, key: str) -> str:
        """The page of an issue named by key.

        The same address `Issue.url` builds, from the same configured
        location, for an issue nobody reported -- one a task merely mentions.
        Built here rather than by the caller so that one place knows the
        shape of a tracker address.
        """
        return f"{self.base_url}/issue/{key}"

    def keys_in(self, text: str | None) -> list[str]:
        """Every mention of a configured project's issue, in order.

        Only the configured projects are recognised.  A pattern for "letters,
        a dash, digits" also matches a version, a standard or a year --
        `GPT-4`, `ISO-8601`, `COVID-19` -- and none of those is an issue.
        Narrowing it to the projects already configured removes that whole
        class of mistake, needs no setting of its own, and means the
        recognised set follows the configuration rather than a pattern
        somebody has to remember to edit.

        A project with no projects configured recognises nothing: there is
        no list to be a member of.
        """
        if not (text and self.projects):
            return []
        pattern = "|".join(re.escape(p) for p in self.projects)
        return [
            f"{project}-{number}"
            for project, number in re.findall(
                rf"\b({pattern})-(\d+)\b", text
            )
        ]

    def rank(self, state: str) -> int:
        """Where a state sits in the configured order, for sorting."""
        return self.states.index(state) if state in self.states else len(self.states)


@dataclass(frozen=True)
class Issue:
    """One issue, in the terms the board needs to draw a row."""

    key: str
    summary: str
    project: str
    state: str
    assignee: str
    base_url: str
    #: What the tracker calls this issue's priority, in its own words -- the
    #: localised name where there is one.  The board shows a priority by the
    #: first letter of this, so that nothing here enumerates the priorities a
    #: tracker happens to define.
    priority: str = ""
    #: The same value's name in the API's own English, which does not change
    #: with the tracker's language.  Not shown to anybody: it is how the board
    #: recognises the least urgent priority, whose word begins with the same
    #: letter as the most urgent one's.
    priority_value: str = ""

    @property
    def url(self) -> str:
        """The issue's own page, for opening in a browser."""
        return f"{self.base_url}/issue/{self.key}"


def load_config(env_path: str | os.PathLike[str] | None = None) -> Config | None:
    """The tracker's configuration, or None when there is none.

    Read from the environment the way the board's own token is, so a value
    already exported in a shell needs no copy in `.env`.

    An absent address, token or assignee means no tracker is configured,
    which is an ordinary board rather than a broken one -- so this answers
    None rather than raising.  The projects and the states have defaults
    because they only narrow what is asked for.
    """
    load_dotenv(env_path, override=False)
    base_url = os.getenv("YOUTRACK_BASE_URL", "").strip().rstrip("/")
    token = os.getenv("YOUTRACK_TOKEN", "").strip()
    assignee = os.getenv("YOUTRACK_ASSIGNEE", "").strip()
    if not (base_url and token and assignee):
        return None
    projects = tuple(
        p.strip() for p in os.getenv("YOUTRACK_PROJECTS", "").split(",") if p.strip()
    )
    states = tuple(
        s.strip() for s in os.getenv("YOUTRACK_STATES", "").split(",") if s.strip()
    ) or ("In progress",)
    return Config(base_url, token, assignee, projects, states)


def _host(base_url: str) -> str:
    """Just the host, for a message that has to fit on one line."""
    return base_url.split("//", 1)[-1].split("/", 1)[0] or base_url


def _custom_fields(raw: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for field in raw.get("customFields") or []:
        value = field.get("value")
        if isinstance(value, dict):
            out[field.get("name")] = value
    return out


def parse(payload: Any, config: Config) -> list[Issue]:
    """The issues in a response that match what was asked for.

    The selection is re-checked here rather than trusted to the query, so a
    change to how the query is built can never quietly widen what the board
    shows.  Ordered by the configured position of an issue's state and then by
    key: the block is not sorted with the day, so it should neither shuffle
    between fetches nor mix the states together.
    """
    if not isinstance(payload, list):
        raise TrackerUnreachable("the tracker returned an unexpected response")
    allowed = set(config.projects)
    issues: list[Issue] = []
    for raw in payload:
        fields = _custom_fields(raw)
        assignee = (fields.get("Assignee") or {}).get("login") or ""
        state = (fields.get("State") or {}).get("name") or ""
        project = (raw.get("project") or {}).get("shortName") or ""
        priority_field = fields.get("Priority") or {}
        # The tracker's own word, falling back to the API's English name: a
        # tracker with no localisation still names its own priorities, and
        # either way the word is the tracker's rather than the board's.
        priority_value = priority_field.get("name") or ""
        priority = priority_field.get("localizedName") or priority_value
        if assignee != config.assignee:
            continue
        if state not in config.states:
            continue
        if allowed and project not in allowed:
            continue
        issues.append(
            Issue(
                key=raw.get("idReadable") or "",
                summary=raw.get("summary") or "",
                project=project,
                state=state,
                assignee=assignee,
                base_url=config.base_url,
                priority=priority,
                priority_value=priority_value,
            )
        )
    return sorted(issues, key=lambda i: (config.rank(i.state), i.key))


def fetch(config: Config, session=None) -> list[Issue]:
    """The issues in progress for the configured person.

    Every way of failing -- no network, no VPN, a refusal, a body that is not
    what was asked for -- arrives as `TrackerUnreachable`, so a caller has one
    thing to catch and can never mistake a tracker problem for its own.
    """
    session = session or requests
    try:
        response = session.get(
            f"{config.base_url}/api/issues",
            headers={
                "Authorization": f"Bearer {config.token}",
                "Accept": "application/json",
            },
            params={
                "query": config.query,
                "fields": ISSUE_FIELDS,
                "$top": MAX_ISSUES,
            },
            timeout=TIMEOUT_SECONDS,
        )
    except requests.RequestException as exc:
        # The usual case is the VPN being down, which fails to connect
        # rather than answering.  The message is short on purpose: it goes
        # on a one-line status bar, and the underlying exception carries the
        # whole request -- the query, and so the assignee -- which is both
        # unreadable there and more than anyone asked to see.  The cause is
        # chained, so it is still there for anyone debugging.
        raise TrackerUnreachable(
            f"could not reach the tracker at {_host(config.base_url)}"
        ) from exc
    if response.status_code != 200:
        raise TrackerUnreachable(
            f"the tracker answered HTTP {response.status_code}"
        )
    try:
        payload = response.json()
    except ValueError as exc:
        raise TrackerUnreachable("the tracker returned a non-JSON body") from exc
    return parse(payload, config)
