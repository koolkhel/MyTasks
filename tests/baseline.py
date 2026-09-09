"""The shared before-picture the regression suites compare against.

These suites ask "is today's board what it was before the change?", which
only means something while the baseline describes today.  It used to be a
frozen file: taken 09-06, still being read on 09-07, reporting a different
day's board as a regression in four suites at once.

So loading it checks the day and refuses rather than misleading.  Refresh it
before making a change, not after -- a baseline taken afterwards agrees with
whatever the change did.
"""
import json, pathlib, sys
from datetime import datetime

HERE = pathlib.Path(__file__).parent
# Beside the suites but excluded from the repository: a baseline describes
# one person's account on one day, so committing it would make the suites
# that read it fail for everybody else, every day.
LOCAL = HERE / "local"
PATH = LOCAL / "baseline.json"
REFRESH = f"  {sys.executable} {HERE / 'capture9.py'} {PATH}"


def load(tz=None):
    LOCAL.mkdir(exist_ok=True)
    if not PATH.exists():
        sys.exit(f"no baseline at {PATH}\nTake one before your change:\n{REFRESH}")
    base = json.load(open(PATH))
    day = str((datetime.now(tz) if tz else datetime.now()).date())
    was = base.get("captured_day")
    if was != day:
        sys.exit(
            f"the baseline describes {was}, but today is {day}.\n"
            f"It cannot say whether today's board changed.  Take a fresh one\n"
            f"BEFORE the change you want to check:\n{REFRESH}"
        )
    return base
