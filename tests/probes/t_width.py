"""How many tasks the store will take at once.

A probe, not a suite: it asserts nothing and is never run by the runner. It
answers one question the design of pasting many lines depends on -- a paste
of N lines starts N writers, and nothing in the client paces them. Whether
that is safe is a fact about the store, and guessing at it would put the
answer in front of a person pasting their week in.

Works on the suites' own token, names everything it creates with the agreed
prefix, and deletes every task it made in a `finally` whatever happens.
"""
import concurrent.futures as _cf
import os
import sys
import time
from datetime import datetime, time as _t, timedelta

_HERE = os.path.dirname(os.path.abspath(__file__))
_TESTS = os.path.dirname(_HERE)
_REPO = os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
sys.path.insert(0, _REPO)
import testtoken as _tt          # the suites' token, not the board's
_tt.adopt()
import singularity
from singularity import SingularityClient, iso_z

#: Far enough out that the day holds nothing of anybody's.
DAY = datetime.now().date() + timedelta(days=900)
WIDTHS = (5, 10, 20, 40)


def main() -> int:
    api = SingularityClient()
    when = iso_z(datetime.combine(DAY, _t.min, tzinfo=api.tz))
    made: list[str] = []
    results = []
    try:
        for width in WIDTHS:
            titles = [f"zz-width-{width}-{n:03d}" for n in range(width)]
            started = time.monotonic()
            errors = []

            def one(title: str):
                return api.create_task(title, start=when, useTime=False)

            with _cf.ThreadPoolExecutor(max_workers=width) as pool:
                for future in [pool.submit(one, t) for t in titles]:
                    try:
                        made.append(future.result().id)
                    except Exception as exc:          # noqa: BLE001 - reporting
                        errors.append(f"{type(exc).__name__}: {exc}")
            took = time.monotonic() - started
            results.append((width, width - len(errors), errors, took))
            print(f"  {width:>3} at once: {width - len(errors)}/{width} created "
                  f"in {took:.2f}s" + (f"  first error: {errors[0]}" if errors else ""))
            # Far enough apart that one width's load does not colour the next.
            time.sleep(25)
    finally:
        left = 0
        for task_id in made:
            try:
                api.delete_task(task_id)
            except Exception:                          # noqa: BLE001 - cleanup
                left += 1
        print(f"\ncleaned up {len(made) - left}/{len(made)} created tasks"
              + (f" -- {left} LEFT BEHIND, delete by hand" if left else ""))
    print("\nanswer:")
    safe = [w for w, made_ok, errs, _ in results if not errs and made_ok == w]
    print(f"  widths that succeeded whole: {safe or 'none'}")
    for width, made_ok, errs, took in results:
        if errs:
            print(f"  {width}: {len(errs)} refused -- {errs[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
