"""How the self-contained suites are collected and run.

Every suite here names the parts it is made of in a `PARTS` tuple, and this
turns each of them into something that can be selected by name, reported on
its own and re-run by itself.  Before this, a suite was addressable only
whole: the smallest failure cost the largest run, and a part that was written
and left out of the tail ran never, with nothing to say so.

Three things this deliberately does not do.

It does not import the board.  Nothing here reaches for `main`, so a suite
that checks it can decide what to draw without an application still finds no
application imported.

It does not supply an event loop.  A part that is a coroutine gets
`asyncio.run`, which is exactly what every suite's own tail did: Textual's
`run_test` is entered inside a part, and the loop it lives in has always
begun and ended there.  A plugin-managed loop would change the lifetime of
the thing under test, and the suites are the instrument.

It does not judge a check.  A part reports by appending to its module's `ok`
list, as it always has; this reads what the part appended and fails the item
when any of it is false.  So every check in a part still runs, even after one
of them has failed -- which is what makes counting the failures mean
something.
"""
import asyncio
import importlib.util
import inspect
import pathlib
import sys

import pytest

HERE = pathlib.Path(__file__).parent
#: The one tier that needs nothing beyond the repository.  A suite in any
#: other directory talks to a real account, a real tracker or a real mailbox,
#: and collecting one means importing it -- which for several of them builds
#: a client and for a few creates tasks.  So a bare `pytest` at the root can
#: reach none of them: it is confined here, and the runner names a file
#: explicitly when it wants one from elsewhere.
SELF_CONTAINED = HERE / "stub"

#: The suites imported in this session, so the run can report their size the
#: way a suite reported it when it ran itself.
_imported: "list" = []


def pytest_collect_file(file_path, parent):
    if file_path.suffix != ".py" or not file_path.name.startswith("t_"):
        return None
    if file_path.parent != SELF_CONTAINED:
        return None
    return Suite.from_parent(parent, path=file_path)


def _import(path: pathlib.Path):
    """Load a suite the way running it as a script would.

    Under its own name, so that two suites holding functions of the same name
    stay apart, and with the file's directory reachable, which is what its
    own preamble arranges when it is run directly.
    """
    name = f"suite_{path.stem}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    _imported.append(module)
    return module


class Suite(pytest.File):
    """One suite file, as the parts it declares."""

    def collect(self):
        module = _import(self.path)
        parts = getattr(module, "PARTS", None)
        if parts is None:
            raise pytest.UsageError(
                f"{self.path.name} declares no PARTS, so there is nothing "
                f"here that says which of its functions are parts and which "
                f"are helpers")
        for part in parts:
            yield Part.from_parent(self, name=part.__name__,
                                   part=part, module=module)


class Part(pytest.Item):
    """One situation a suite sets up and checks."""

    def __init__(self, *, part, module, **kw):
        super().__init__(**kw)
        self.part = part
        self.module = module

    def runtest(self):
        # Measured before and after rather than held across the run: a suite
        # that keeps more than one list is read as the lists joined, and the
        # joining makes a new list each time.
        first = len(checks_of(self.module))
        if inspect.iscoroutinefunction(self.part):
            asyncio.run(self.part())
        else:
            self.part()
        mine = checks_of(self.module)[first:]
        failed = sum(1 for good in mine if not good)
        if failed:
            raise PartFailed(
                f"{failed} of {len(mine)} checks failed in {self.name}; the "
                f"FAIL lines above name them and say what each got")

    def repr_failure(self, excinfo):
        if isinstance(excinfo.value, PartFailed):
            return str(excinfo.value)
        return super().repr_failure(excinfo)

    def reportinfo(self):
        return self.path, None, self.name


def checks_of(module):
    """The one list a suite appends its checks to, or the first of several.

    A suite that keeps two lists says so in `CHECKS`; everything else keeps
    the single `ok` every suite here has always had.
    """
    several = getattr(module, "CHECKS", None)
    if several:
        return [good for one in several for good in one]
    return module.ok


class PartFailed(Exception):
    """Checks failed in a part.  They have already said so themselves."""


def pytest_sessionfinish(session, exitstatus):
    """Say how many checks the suite made, as its own tail used to.

    The runner reads this line to report a suite's size, and the list of
    known failures reads it to tell a recorded failure from a new one.  It is
    printed here so that neither had to change when the suites stopped
    driving themselves.
    """
    for module in _imported:
        if getattr(module, "ok", None) is not None:
            made = checks_of(module)
            print(f"\n{sum(made)}/{len(made)} checks passed")
