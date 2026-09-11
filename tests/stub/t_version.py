"""The version an issue is against: read from a configured field, or not at all.

Invented issue keys, invented project names, invented versions.  Nothing here
comes from a real tracker, and no request leaves the machine.
"""
import sys
import os as _os
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0, _TESTS)
sys.path.insert(0, _REPO)
import tracker
from tracker import Config, ISSUE_FIELDS, _custom_fields, _first, _names

ok = []
def chk(label, cond, extra=""):
    ok.append(bool(cond))
    print(f"  [{'PASS' if cond else 'FAIL'}] {label}" + (f"  {extra}" if extra else ""))

VERSION_FIELD = "Fix versions"


def cfg(version_field=VERSION_FIELD, states=("In progress",), projects=()):
    return Config(base_url="https://tracker.invalid", token="t",
                  assignee="somebody", projects=projects, states=states,
                  version_field=version_field)


def issue(key="AAA-1", fields=(), project="AAA"):
    """One issue as the tracker hands it back, with these custom fields."""
    return {
        "idReadable": key,
        "summary": "a summary nobody wrote",
        "project": {"shortName": project},
        "customFields": [
            {"name": "Assignee", "value": {"login": "somebody"}},
            {"name": "State", "value": {"name": "In progress"}},
            *fields,
        ],
    }


#: One of each shape a custom field's value can have.
SHAPES = (
    {"name": "Component", "value": {"name": "a-component"}},      # single
    {"name": VERSION_FIELD, "value": [{"name": "1.6-1"},
                                      {"name": "1.7"}]},          # several
    {"name": "Subsystems", "value": []},                          # an empty list
    {"name": "Due Date", "value": 1750000000},                    # a bare number
    {"name": "Release Notes", "value": None},                     # absent
)


def t_shapes():
    print("1.1 every shape a custom field's value can have")
    fields = _custom_fields(issue(fields=SHAPES))
    chk("a single value is kept, as a list of one",
        fields.get("Component") == [{"name": "a-component"}],
        repr(fields.get("Component")))
    chk("several are kept, in the tracker's order",
        [v["name"] for v in fields.get(VERSION_FIELD, [])] == ["1.6-1", "1.7"],
        repr(fields.get(VERSION_FIELD)))
    chk("an empty list is kept, and is empty",
        fields.get("Subsystems") == [], repr(fields.get("Subsystems")))
    chk("a bare number is dropped, as it always was",
        "Due Date" not in fields, repr(fields.get("Due Date")))
    chk("an absent value is dropped",
        "Release Notes" not in fields, repr(fields.get("Release Notes")))
    chk("a field the issue does not carry is simply not there",
        "Nothing At All" not in fields)
    chk("nothing that is not a mapping survives inside a list",
        _custom_fields({"customFields": [
            {"name": "Mixed", "value": [{"name": "kept"}, "dropped", 7]}
        ]})["Mixed"] == [{"name": "kept"}])


def t_readers():
    print("1.1 reading one value or all of them")
    fields = _custom_fields(issue(fields=SHAPES))
    chk("the first of several", _first(fields, VERSION_FIELD) == {"name": "1.6-1"})
    chk("the first of one", _first(fields, "Component") == {"name": "a-component"})
    chk("the first of none is empty, not an error",
        _first(fields, "Subsystems") == {} and _first(fields, "Absent") == {})
    chk("every name, in order", _names(fields, VERSION_FIELD) == ("1.6-1", "1.7"))
    chk("no names where there are none", _names(fields, "Absent") == ())


def t_issue_versions():
    print("1.2 the issue carries what the configured field holds")
    several = tracker.parse([issue(fields=SHAPES)], cfg())[0]
    chk("several versions, in order", several.versions == ("1.6-1", "1.7"),
        repr(several.versions))
    one = tracker.parse(
        [issue(fields=({"name": VERSION_FIELD, "value": [{"name": "2.0"}]},))],
        cfg())[0]
    chk("one version", one.versions == ("2.0",), repr(one.versions))
    empty = tracker.parse(
        [issue(fields=({"name": VERSION_FIELD, "value": []},))], cfg())[0]
    chk("a field carried but empty is no version",
        empty.versions == (), repr(empty.versions))
    missing = tracker.parse([issue()], cfg())[0]
    chk("a field the issue does not carry is no version",
        missing.versions == (), repr(missing.versions))
    unnamed = tracker.parse([issue(fields=SHAPES)], cfg(version_field=""))[0]
    chk("no field configured is no version",
        unnamed.versions == (), repr(unnamed.versions))
    elsewhere = tracker.parse([issue(fields=SHAPES)],
                              cfg(version_field="Affected versions"))[0]
    chk("a different field configured reads that one, not this one",
        elsewhere.versions == (), repr(elsewhere.versions))
    chk("and the rest of the issue is untouched by any of it",
        (several.key, several.state, several.assignee, several.project)
        == ("AAA-1", "In progress", "somebody", "AAA"))


def t_reader_absent():
    print("1.2 the field's name, on the absent case only")
    # Only the absent case is asserted.  python-dotenv finds the real `.env`
    # by walking up from the module beside this one, so emptying the
    # environment does not hide a configured field -- a check asserting on a
    # configured name would pass or fail by whose machine ran it.
    import tempfile
    kept = _os.environ.pop("YOUTRACK_VERSION_FIELD", None)
    empty = _os.path.join(tempfile.mkdtemp(prefix="version."), ".env")
    try:
        open(empty, "w").close()
        for key, value in (("YOUTRACK_BASE_URL", "https://tracker.invalid"),
                           ("YOUTRACK_TOKEN", "t"),
                           ("YOUTRACK_ASSIGNEE", "somebody")):
            _os.environ.setdefault(key, value)
        loaded = tracker.load_config(empty)
        chk("no YOUTRACK_VERSION_FIELD means no field",
            loaded is not None and loaded.version_field == "",
            repr(loaded and loaded.version_field))
    finally:
        if kept is not None:
            _os.environ["YOUTRACK_VERSION_FIELD"] = kept


class Recorder:
    """A session that answers nothing and remembers what it was asked."""

    def __init__(self):
        self.calls = []

    def get(self, url, **kw):
        self.calls.append((url, kw))
        return self

    status_code = 200

    @staticmethod
    def json():
        return []


def t_costs_nothing():
    print("1.3 reading it costs no further request")
    chk("the request asks for exactly what it always asked for",
        ISSUE_FIELDS == ("idReadable,summary,project(shortName),updated,"
                         "customFields(name,value(name,localizedName,login))"),
        ISSUE_FIELDS)
    chk("and names no particular field beyond that",
        VERSION_FIELD not in ISSUE_FIELDS and "version" not in ISSUE_FIELDS)
    with_field, without = Recorder(), Recorder()
    tracker.fetch(cfg(), session=with_field)
    tracker.fetch(cfg(version_field=""), session=without)
    chk("one request either way",
        len(with_field.calls) == len(without.calls) == 1,
        f"{len(with_field.calls)} and {len(without.calls)}")
    chk("to the same address", with_field.calls[0][0] == without.calls[0][0])
    chk("with the same parameters",
        with_field.calls[0][1]["params"] == without.calls[0][1]["params"],
        str(with_field.calls[0][1]["params"]))
    chk("and the configured field is in none of them",
        VERSION_FIELD not in str(with_field.calls[0][1]))


for fn in (t_shapes, t_readers, t_issue_versions, t_reader_absent,
           t_costs_nothing):
    fn()

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
