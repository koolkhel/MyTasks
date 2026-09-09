"""Stubbed client + synthetic tasks for driving TaskApp under Pilot.

No real task data is used anywhere: every task here is generated.
"""
import sys, threading, itertools
from datetime import date, datetime, time, timedelta
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _REPO)
import singularity
from singularity import (Task, Listing, Bucket, SingularityError, ApiError,
                         iso_z, local_tz, sort_for_display, CHECKED, CANCELLED, EMPTY)

try:
    import ical
except ImportError:          # the pre-change board, which reads no calendar
    ical = None
# The board reads the machine's calendar wherever one is configured.  A suite
# drives synthetic data and nothing else -- no real calendar is ever read
# here -- so every app built under this harness starts with none.  A suite
# that wants events sets `app.calendar_config` itself.
if ical is not None:
    ical.load_config = lambda *a, **k: None
try:
    import mail as _mail
except ImportError:            # the pre-change board, which reads no mailbox
    _mail = None
if _mail is not None:
    _mail.load_config = lambda *a, **k: None
try:
    import gateway as _gateway
except ImportError:            # the pre-change board, which reaches no server
    _gateway = None
# Likewise, and for a stronger reason: this one holds an account's credentials
# and can move a person's mail.  Every board built here starts with no gateway,
# so a suite that has not deliberately substituted a server cannot reach one
# however it presses keys.
if _gateway is not None:
    _gateway.load_config = lambda *a, **k: None

TZ = local_tz()

def mk(tid, title, start=None, checked=0, deferred=False, project=None, deadline=None, timed=False):
    raw = {"id": tid, "title": title, "checked": checked, "deferred": deferred,
           "useTime": timed}
    if start is not None:
        raw["start"] = iso_z(datetime.combine(start, time.min, tzinfo=TZ))
    if project: raw["projectId"] = project
    if deadline is not None:
        raw["deadline"] = iso_z(datetime.combine(deadline, time.min, tzinfo=TZ))
    return Task(raw)


class StubClient:
    """Records calls, can be made slow or made to fail per method."""

    def __init__(self, tasks=None, reference=None, filed_out=0):
            self.tz = TZ
            self.store = {t.id: t for t in (tasks or [])}
            self.reference = reference
            self.filed_out = filed_out
            self.calls = []                # (method, args)
            self.gate = None               # threading.Event writes wait on
            self.fail = {}                 # method name -> exception
            self.fail_ids = {}             # (method, id) -> exception
            self._n = itertools.count(1)
            self.lock = threading.Lock()
            self.green = None              # the tag that orders a task first
            self.tag_titles = {}           # tag id -> title, for tag_title()

    # -- bookkeeping -------------------------------------------------------
    READS = {"project_names", "tasks_at", "tasks_for_day"}

    def _record(self, name, *args):
        with self.lock:
            self.calls.append((name, args))
        # Only writes are held: gating reads would stall the initial load.
        if self.gate is not None and name not in self.READS:
            self.gate.wait(5)
        key = (name, args[0] if args else None)
        if key in self.fail_ids: raise self.fail_ids[key]
        if name in self.fail: raise self.fail[name]

    def count(self, name):
        return sum(1 for c, _ in self.calls if c == name)

    # -- reads -------------------------------------------------------------
    def project_names(self, **kw):
        self._record("project_names")
        return {}

    def tasks_at(self, position, **kw):
        self._record("tasks_at", position)
        if isinstance(position, Bucket):
            rows = [t for t in self.store.values()
                    if not t.done and not t.cancelled and t.start is None
                    and t.deferred == position.deferred
                    and not (position is Bucket.INBOX and t.project_id)]
            return Listing(sort_for_display(rows, self.tz), self.filed_out)
        rows = [t for t in self.store.values()
                if (t.local_start(self.tz) and t.local_start(self.tz).date() == position)]
        if self.reference is not None:
            extra = [t for t in self.store.values()
                     if t.id not in {r.id for r in rows}
                     and t.past_due_since(self.reference, self.tz)]
            rows = rows + extra
            return Listing(sort_for_display(rows, self.tz, self.reference),
                           past_due=sum(1 for t in rows if t.past_due_since(self.reference, self.tz)),
                           reference=self.reference)
        return Listing(sort_for_display(rows, self.tz))

    def tasks_for_day(self, day=None, include_done=True, **filters):
        """A day's tasks, as the real client answers.

        A read: what a promotion asks for to find the order past everything
        the day already holds.
        """
        self._record("tasks_for_day", day)
        return self.tasks_at(day or datetime.now(self.tz).date())

    # -- writes ------------------------------------------------------------
    def tag_title(self, tag_id):
        self._record("tag_title", tag_id)
        # Unknown ids resolve to nothing, as the real client answers for a
        # tag the account does not have.
        return self.tag_titles.get(tag_id, "Зеленая" if tag_id == self.green else None)

    def task_tags(self, tid):
        self._record("task_tags", tid)
        return tuple(self.store[tid].raw.get("tags") or ())

    def set_tags(self, tid, tags):
        self._record("set_tags", tid, list(tags))
        self.store[tid].raw["tags"] = list(tags)
        return self.store[tid]

    def set_done(self, task, done):
        self._record("set_done", task.id, done)
        self.store[task.id].raw["checked"] = CHECKED if done else EMPTY

    def cancel_task(self, tid):
        self._record("cancel_task", tid)
        self.store[tid].raw["checked"] = CANCELLED

    def update_task(self, tid, **fields):
        self._record("update_task", tid, tuple(sorted(fields)))
        self.store[tid].raw.update(fields)
        return self.store[tid]

    def set_schedule(self, tid, position, use_time=False):
        self._record("set_schedule", tid, position)
        if isinstance(position, Bucket):
            self.store[tid].raw.update({"start": None, "deferred": position.deferred})
        else:
            self.store[tid].raw.update({
                "start": iso_z(datetime.combine(position, time.min, tzinfo=self.tz)),
                "useTime": use_time, "deferred": False})
        return self.store[tid]

    def complete_today(self, tid):
        self._record("complete_today", tid)

    def done_for_today(self, task):
        try:
            self.complete_today(task.id)
        except ApiError as exc:
            if exc.status != 422: raise
        tomorrow = datetime.now(self.tz).date() + timedelta(days=1)
        return self.set_schedule(task.id, tomorrow)

    def delete_task(self, tid):
        self._record("delete_task", tid)
        self.store.pop(tid, None)

    def set_project(self, tid, project_id):
        self._record("set_project", tid, project_id)
        self.store[tid].raw["projectId"] = project_id
        return self.store[tid]

    def restore(self, tid, fields):
        self._record("restore", tid, tuple(sorted(fields)))
        fields=dict(fields); project=fields.pop("projectId", None)
        self.store[tid].raw.update(fields)
        if project is not None: self.store[tid].raw["projectId"]=project
        return self.store[tid]

    def create_task(self, title, **fields):
        self._record("create_task", title)
        tid = f"T-new-{next(self._n)}"
        t = Task({"id": tid, "title": title, "checked": 0, **fields})
        self.store[tid] = t
        return t
