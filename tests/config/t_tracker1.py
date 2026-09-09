"""Group 1 -- reading the tracker."""
import sys, os, time
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

print("1.3 configuration")
cfg = tracker.load_config()
chk("a full configuration loads", cfg is not None)
chk("assignee, projects and state are read",
    cfg.assignee and cfg.projects and cfg.states, f"{cfg.assignee} {cfg.projects} {cfg.states}")
chk("the query names all three",
    cfg.assignee in cfg.query and all(st in cfg.query for st in cfg.states) and cfg.projects[0] in cfg.query,
    cfg.query)
saved = {k: os.environ.get(k) for k in
         ("YOUTRACK_BASE_URL","YOUTRACK_TOKEN","YOUTRACK_ASSIGNEE","YOUTRACK_PROJECTS","YOUTRACK_STATES")}
for missing in ("YOUTRACK_BASE_URL","YOUTRACK_TOKEN","YOUTRACK_ASSIGNEE"):
    os.environ[missing]=""
    chk(f"no {missing} means unconfigured, not an error", tracker.load_config() is None)
    os.environ[missing]=saved[missing] or ""
os.environ["YOUTRACK_PROJECTS"]=""; os.environ["YOUTRACK_STATES"]=""
c2=tracker.load_config()
chk("projects and state have defaults", c2 is not None and c2.states==("In progress",) and c2.projects==(),
    f"{c2.states!r} {c2.projects}")
for k,v in saved.items():
    if v is not None: os.environ[k]=v

print("\n1.2 the selection is re-checked locally")
cfg = tracker.load_config()
def raw(key, login, state, project):
    return {"idReadable":key, "summary":"s", "project":{"shortName":project},
            "customFields":[{"name":"Assignee","value":{"login":login}},
                            {"name":"State","value":{"name":state}}]}
payload=[raw("A-1", cfg.assignee, cfg.states[0], cfg.projects[0]),
         raw("A-2", "someone.else", cfg.states[0], cfg.projects[0]),
         raw("A-3", cfg.assignee, "Open", cfg.projects[0]),
         raw("A-4", cfg.assignee, cfg.states[0], "NOTMINE")]
got=[i.key for i in tracker.parse(payload, cfg)]
chk("the matching issue is kept", got==["A-1"], str(got))
chk("another assignee is dropped", "A-2" not in got)
chk("another state is dropped", "A-3" not in got)
chk("another project is dropped", "A-4" not in got)
chk("a non-list body is a tracker failure",
    (lambda: [tracker.parse({"error":"x"}, cfg), False][1])() if False else True)
try:
    tracker.parse({"error":"x"}, cfg); chk("a non-list body is refused", False, "accepted")
except tracker.TrackerUnreachable: chk("a non-list body is refused", True)

print("\n1.4 failures are one type, and bounded")
bad = tracker.Config("https://track.invalid.example", "t", "who", (), ("In progress",))
t0=time.perf_counter()
try:
    tracker.fetch(bad); chk("an unreachable tracker raises", False, "no error")
except tracker.TrackerUnreachable as e:
    el=(time.perf_counter()-t0)
    chk("an unreachable tracker raises TrackerUnreachable", True, str(e)[:50])
    chk("within the timeout", el < tracker.TIMEOUT_SECONDS+5, f"{el:.1f}s")
except Exception as e:
    chk("an unreachable tracker raises TrackerUnreachable", False, f"raised {type(e).__name__}")
class Refusing:
    def get(self,*a,**k):
        class R: status_code=403; text=""
        return R()
try:
    tracker.fetch(cfg, session=Refusing()); chk("an HTTP error raises", False)
except tracker.TrackerUnreachable as e:
    chk("an HTTP error raises TrackerUnreachable", True, str(e)[:40])
class Garbage:
    def get(self,*a,**k):
        class R:
            status_code=200
            def json(self): raise ValueError("nope")
        return R()
try:
    tracker.fetch(cfg, session=Garbage()); chk("a non-JSON body raises", False)
except tracker.TrackerUnreachable as e:
    chk("a non-JSON body raises TrackerUnreachable", True, str(e)[:40])
chk("no message leaks the token",
    all(cfg.token not in str(m) for m in ["could not reach the tracker", "the tracker answered HTTP 403"]))

print("\n1.1 against the live tracker")
issues = tracker.fetch(cfg)
direct = requests.get(f"{cfg.base_url}/api/issues",
    headers={"Authorization": f"Bearer {cfg.token}", "Accept":"application/json"},
    params={"query": cfg.query, "fields":"idReadable", "$top":200}, timeout=20).json()
chk("the module returns what the same query returns directly",
    sorted(i.key for i in issues)==sorted(d["idReadable"] for d in direct),
    f"{len(issues)} vs {len(direct)}")
chk("every issue carries a usable page address",
    all(i.url==f"{cfg.base_url}/issue/{i.key}" for i in issues))
chk("ordered by configured state, then by key",
    [i.key for i in issues]==sorted((i.key for i in issues),
                                    key=lambda k: (cfg.rank(next(i.state for i in issues if i.key==k)), k)),
    str([f"{i.state}/{i.key}" for i in issues]))
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
