"""Group 1 -- several configured states."""
import sys, os
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0,_REPO)
import requests, tracker
ok=[]
def chk(l,c,e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}"+(f"  {e}" if e else ""))
KEYS=("YOUTRACK_STATES","YOUTRACK_BASE_URL","YOUTRACK_TOKEN","YOUTRACK_ASSIGNEE","YOUTRACK_PROJECTS")
saved_all={k: os.environ.get(k) for k in KEYS}
saved=saved_all["YOUTRACK_STATES"]

print("1.1 the setting is a list, in the order written")
os.environ["YOUTRACK_STATES"]="In review, In progress"
c=tracker.load_config()
chk("read back in the order written", c.states==("In review","In progress"), str(c.states))
chk("whitespace around each entry is ignored", all(s==s.strip() for s in c.states), str(c.states))
os.environ["YOUTRACK_STATES"]="  ,, In progress ,  "
chk("empty entries are dropped", tracker.load_config().states==("In progress",),
    str(tracker.load_config().states))
os.environ["YOUTRACK_STATES"]=""
chk("an empty setting keeps the default", tracker.load_config().states==("In progress",),
    str(tracker.load_config().states))
# truly absent means absent from BOTH the environment and .env; popping the
# variable only falls back to .env, which is the precedence we want
os.environ.pop("YOUTRACK_STATES")
import tempfile
with tempfile.NamedTemporaryFile("w", suffix=".env", delete=False) as f:
    f.write("YOUTRACK_BASE_URL=https://t.example\nYOUTRACK_TOKEN=x\nYOUTRACK_ASSIGNEE=me\n")
    tmp=f.name
for k in ("YOUTRACK_BASE_URL","YOUTRACK_TOKEN","YOUTRACK_ASSIGNEE"): os.environ.pop(k, None)
chk("absent from both environment and .env keeps the default",
    tracker.load_config(tmp).states==("In progress",), str(tracker.load_config(tmp).states))
chk("and the environment still wins where it is set",
    (os.environ.__setitem__("YOUTRACK_STATES","Blocked"),
     tracker.load_config(tmp).states)[1]==("Blocked",))
os.environ.pop("YOUTRACK_STATES", None)
# put the real environment back: the checks below fetch for real
for _k,_v in saved_all.items():
    if _v is None: os.environ.pop(_k, None)
    else: os.environ[_k]=_v
if saved is not None: os.environ["YOUTRACK_STATES"]=saved
c=tracker.load_config()

print("\n1.2 the query names every state")
one=tracker.Config(c.base_url,c.token,c.assignee,c.projects,("In progress",))
chk("one state produces the single-state form",
    "State: {In progress} " in one.query+" ", one.query)
chk("two states produce the comma-separated braced form",
    "State: {In progress}, {In review}" in c.query, c.query)
def keys(cfg):
    return sorted(i.key for i in tracker.fetch(cfg))
a=keys(one)
b=keys(tracker.Config(c.base_url,c.token,c.assignee,c.projects,("In review",)))
both=keys(c)
chk("the two-state query returns the union of the single-state ones",
    sorted(a+b)==both, f"{len(a)}+{len(b)} vs {len(both)}")

print("\n1.3 the local re-check uses the whole list")
def raw(key, login, state, project):
    return {"idReadable":key,"summary":"s","project":{"shortName":project},
            "customFields":[{"name":"Assignee","value":{"login":login}},
                            {"name":"State","value":{"name":state}}]}
P=c.projects[0]
payload=[raw("A-1",c.assignee,"In progress",P), raw("A-2",c.assignee,"In review",P),
         raw("A-3",c.assignee,"Open",P), raw("A-4","other","In review",P),
         raw("A-5",c.assignee,"In review","NOPE")]
got=[i.key for i in tracker.parse(payload,c)]
chk("issues in either configured state are kept", set(got)=={"A-1","A-2"}, str(got))
chk("an unconfigured state is dropped", "A-3" not in got)
chk("the assignee check still applies", "A-4" not in got)
chk("the project check still applies", "A-5" not in got)

print("\n1.4 ordered by configured state, then key")
payload=[raw("Z-9",c.assignee,"In progress",P), raw("A-1",c.assignee,"In review",P),
         raw("A-2",c.assignee,"In progress",P), raw("B-1",c.assignee,"In review",P)]
got=[(i.state,i.key) for i in tracker.parse(payload,c)]
chk("the first configured state leads",
    [s for s,_ in got]==["In progress","In progress","In review","In review"], str(got))
chk("by key within a state", [k for s,k in got if s=="In progress"]==["A-2","Z-9"], str(got))
chk("the same data gives the same order twice",
    got==[(i.state,i.key) for i in tracker.parse(payload,c)])
rev=tracker.Config(c.base_url,c.token,c.assignee,c.projects,("In review","In progress"))
got2=[s for s,_ in [(i.state,i.key) for i in tracker.parse(payload,rev)]]
chk("reversing the configuration reverses the block",
    got2==["In review","In review","In progress","In progress"], str(got2))

print("\n1.5 a state matching nothing contributes nothing")
plus=tracker.Config(c.base_url,c.token,c.assignee,c.projects,c.states+("No Such State",))
got=[i.key for i in tracker.parse(payload,plus)]
chk("the other states' issues are unchanged", set(got)=={"Z-9","A-1","A-2","B-1"}, str(got))
chk("and it raises nothing", True)

print("\n1.6 against the live tracker")
issues=tracker.fetch(c)
chk("both states come back", {i.state for i in issues}<=set(c.states) and len(issues)>0,
    str(sorted({i.state for i in issues})))
chk("the first-configured state leads",
    [c.rank(i.state) for i in issues]==sorted(c.rank(i.state) for i in issues),
    str([i.state for i in issues][:3]))
print("\n1.4 the priority arrives with the issue")
# The board shows a tracker priority as one letter, taken from the word the
# tracker itself uses for it.  The request already asks for every custom
# field, so the priority was arriving all along -- only the localised word had
# to be asked for, which is what these check.
chk("the request asks for the tracker's own word for a value",
    "localizedName" in tracker.ISSUE_FIELDS, tracker.ISSUE_FIELDS)
chk("and asks for nothing else new",
    tracker.ISSUE_FIELDS.count("customFields") == 1
    and tracker.ISSUE_FIELDS.replace(",localizedName", "")
    == "idReadable,summary,project(shortName),updated,"
       "customFields(name,value(name,login))",
    tracker.ISSUE_FIELDS)

def with_priority(key, value):
    """One issue, with whatever Priority field `value` describes."""
    r = raw(key, c.assignee, c.states[0], P)
    if value is not None:
        r["customFields"].append({"name": "Priority", "value": value})
    return r

#: Both names, the tracker's word and the API's English one.
both = tracker.parse([with_priority(
    "P-1", {"name": "Show-stopper", "localizedName": "Неотложная"})], c)[0]
chk("the tracker's own word is kept", both.priority == "Неотложная", both.priority)
chk("and the API's English name beside it",
    both.priority_value == "Show-stopper", both.priority_value)

#: A tracker with no localisation still names its own priorities.
english = tracker.parse([with_priority("P-2", {"name": "Critical"})], c)[0]
chk("with no localised word, the English name stands in",
    english.priority == "Critical", english.priority)
chk("and is still reported as the value it is",
    english.priority_value == "Critical", english.priority_value)

#: No priority set, and no Priority field at all.
unset = tracker.parse([with_priority("P-3", None)], c)[0]
chk("an issue with no priority field reports nothing",
    (unset.priority, unset.priority_value) == ("", ""),
    f"{unset.priority!r} {unset.priority_value!r}")
# A field present but empty is how the tracker says "not set": its value is
# null, which `_custom_fields` drops for being no dict at all.
null = tracker.parse([{"idReadable": "P-4", "summary": "s",
                       "project": {"shortName": P},
                       "customFields": [
                           {"name": "Assignee", "value": {"login": c.assignee}},
                           {"name": "State", "value": {"name": c.states[0]}},
                           {"name": "Priority", "value": None}]}], c)[0]
chk("nor does one whose priority is unset",
    (null.priority, null.priority_value) == ("", ""),
    f"{null.priority!r} {null.priority_value!r}")

chk("an Issue built without a priority still builds",
    tracker.Issue(key="K", summary="s", project=P, state=c.states[0],
                  assignee=c.assignee, base_url="https://t.invalid").priority == "")

print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
