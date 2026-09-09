"""The environment a suite that talks to the task store is launched with.

The account has two tokens: the one the board uses, and one for the suites.
A test run spends its own quota, so exhausting it -- which a full run can --
leaves the board the person is actually using still able to answer.

Read from `SINGULARITY_TEST_TOKEN` and handed to the suite as
`SINGULARITY_TOKEN`, because nothing in the product knows about a test token
and nothing should: the suites exercise the same code path a real run takes.
Where no test token is configured the suite's own environment is passed
through unchanged, so a checkout with one token still works.
"""
import os

from dotenv import dotenv_values


def adopt(repo_root=None):
    """Make this process use the suites' token, not the board's.

    Called by every suite that talks to the task store, before it builds a
    client.  The runner also hands the token to the suites it launches, but a
    suite run directly -- which is how a failure gets narrowed down -- would
    otherwise reach for the board's own token and spend the quota the person
    is working in.

    Sets `SINGULARITY_TOKEN` in this process only, and only when a suites'
    token is configured; a checkout with one token is left alone.  Answers
    the label and last four characters, never the token.
    """
    root = repo_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    configured = dotenv_values(os.path.join(root, ".env")) or {}
    test_token = (configured.get("SINGULARITY_TEST_TOKEN") or "").strip()
    if test_token:
        # Set, not defaulted: the board's token is very likely already in the
        # environment or in .env, and the point is to override it.
        os.environ["SINGULARITY_TOKEN"] = test_token
    return which_token(root)


def child_env(repo_root, base=None):
    """The environment to launch a store-tier suite with."""
    env = dict(os.environ if base is None else base)
    configured = dotenv_values(os.path.join(repo_root, ".env")) or {}
    test_token = (configured.get("SINGULARITY_TEST_TOKEN") or "").strip()
    if test_token:
        env["SINGULARITY_TOKEN"] = test_token
    return env


def which_token(repo_root):
    """Whether a run will use the suites' token or the board's; for reporting.

    Returns a label and the last four characters, never the token.
    """
    configured = dotenv_values(os.path.join(repo_root, ".env")) or {}
    test_token = (configured.get("SINGULARITY_TEST_TOKEN") or "").strip()
    if test_token:
        return "the suites' own token", test_token[-4:]
    board = (configured.get("SINGULARITY_TOKEN") or os.getenv("SINGULARITY_TOKEN") or "").strip()
    return "the board's token", board[-4:] if board else "none"
