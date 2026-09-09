"""Group 1 -- the twin table and the expansion helper."""
import sys
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0,_REPO)
from main import KEY_TWINS, keys
ok=[]
def chk(l,c,e=""):
    ok.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {l}"+(f"  {e}" if e else ""))

print("1.1 the table")
for k,v in [("a","ф"),("k","л"),("K","Л"),("q","й"),("j","о"),("s","ы"),("d","в"),
            ("e","у"),("x","ч"),("o","щ"),("i","ш"),("t","е"),("r","к"),("h","р"),
            ("l","д"),("J","О"),("m","ь"),("p","з"),("c","с"),("n","т"),("y","н")]:
    chk(f"{k} -> {v}", KEY_TWINS.get(k)==v, f"got {KEY_TWINS.get(k)!r}")
chk("all 26 lowercase letters covered",
    all(c in KEY_TWINS for c in "abcdefghijklmnopqrstuvwxyz"),
    str([c for c in "abcdefghijklmnopqrstuvwxyz" if c not in KEY_TWINS]))
chk("all 26 uppercase letters covered",
    all(c in KEY_TWINS for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
chk("all 7 punctuation positions covered",
    all(n in KEY_TWINS for n in ("left_square_bracket","right_square_bracket",
        "semicolon","apostrophe","comma","full_stop","slash")))
vals=list(KEY_TWINS.values())
dup=[v for v in set(vals) if vals.count(v)>1]
chk("no character is the twin of two different keys", not dup, str(dup))
chk("every twin is non-empty and differs from its key",
    all(v and v!=k for k,v in KEY_TWINS.items()))
chk("uppercase twins are the uppercase of the lowercase twins",
    all(KEY_TWINS[c.upper()]==KEY_TWINS[c].upper() for c in "abcdefghijklmnopqrstuvwxyz"))

print("\n1.2 the two keyed by Textual's names")
chk("full_stop -> ю", KEY_TWINS["full_stop"]=="ю", KEY_TWINS.get("full_stop",""))
chk("question_mark -> comma (RU puts a comma where ? is)",
    KEY_TWINS["question_mark"]=="comma", KEY_TWINS.get("question_mark",""))
chk("slash -> full_stop (RU types . on the / key)",
    KEY_TWINS["slash"]=="full_stop", KEY_TWINS.get("slash",""))
chk("expanding full_stop", keys("full_stop")=="full_stop,ю", keys("full_stop"))
chk("expanding question_mark", keys("question_mark")=="question_mark,comma", keys("question_mark"))

print("\n1.3 the helper")
for spec,want in [("a","a,ф"), ("j,down","j,down,о"), ("K","K,Л"), ("escape","escape"),
                  ("space","space"), ("backspace,delete","backspace,delete"),
                  ("k,up","k,up,л"), ("h,left","h,left,р"), ("l,right","l,right,д"),
                  ("escape,n","escape,n,т"), ("escape,question_mark,q","escape,question_mark,q,comma,й"),
                  ("escape,enter,q","escape,enter,q,й")]:
    chk(f"keys({spec!r})", keys(spec)==want, f"got {keys(spec)!r} wanted {want!r}")
chk("the first key is always unchanged, so the key bar still shows English",
    all(keys(s).split(",")[0]==s.split(",")[0]
        for s in ["a","j,down","K","full_stop","question_mark","escape,n"]))
chk("expansion is idempotent in the keys it names (no key repeated)",
    all(len(keys(s).split(","))==len(set(keys(s).split(",")))
        for s in ["a","j,down","escape,question_mark,q","escape,n","k,up"]))
print(f"\n{sum(ok)}/{len(ok)} checks passed")
sys.exit(0 if all(ok) else 1)
