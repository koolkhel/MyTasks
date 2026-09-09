"""What a suite acts on: the suites' own account, and nobody's real mail.

The account has two tokens: the one the board uses, and one for the suites.
A test run spends its own quota, so exhausting it -- which a full run can --
leaves the board the person is actually using still able to answer.

Read from `SINGULARITY_TEST_TOKEN` and handed to the suite as
`SINGULARITY_TOKEN`, because nothing in the product knows about a test token
and nothing should: the suites exercise the same code path a real run takes.
Where no test token is configured the suite's own environment is passed
through unchanged, so a checkout with one token still works.

The same call also keeps the suite out of the person's mail.  Once a mail
directory and a gateway are configured, an ordinary board reads real folders
and can move real messages -- so a suite that built one and pressed a key
would archive somebody's mail.  Only the gateway tier may reach a mail
server, and it says so by not calling this at all.
"""
import os
import sys

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
    keep_out_of_mail(root)
    return which_token(root)


def keep_out_of_mail(repo_root=None):
    """Make a board built in this process read no mailbox and reach no server.

    Done by answering None from the two functions that say where the mailbox
    and the gateway are, which is the same "not configured" a board without
    them has -- so nothing here is a special case the product would not meet
    in ordinary use.

    A suite that wants a mailbox sets `app.mail_config` itself, to a copy of
    the fixture; the suites that reach a real mail server are the gateway
    tier, and they do not call this.
    """
    root = repo_root or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root not in sys.path:
        sys.path.insert(0, root)
    for name in ("mail", "gateway"):
        try:
            module = __import__(name)
        except ImportError:
            continue          # a checkout predating that module
        module.load_config = lambda *a, **k: None


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
