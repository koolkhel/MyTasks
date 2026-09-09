import asyncio, sys
import os as _os, sys as _sys
# Where this suite is, and therefore where its neighbours and the board are.
# Nothing here may name an absolute path: the suites were unrunnable anywhere
# but the machine that wrote them precisely because they did.
_TESTS = _os.path.dirname(_os.path.abspath(__file__))
_TESTS = _os.path.dirname(_TESTS)
_REPO = _os.path.dirname(_TESTS)
sys.path.insert(0,_REPO)
from textual.app import App, ComposeResult
from textual.widgets import Static, Input
from textual.binding import Binding
seen=[]
class Probe(App):
    BINDINGS=[Binding("ф","noop","Add(ru)"), Binding("Л","noop","MoveUp(ru)")]
    def compose(self)->ComposeResult: yield Static("x")
    def on_key(self,e): seen.append((e.key, e.character))
    def action_noop(self): seen.append(("ACTION FIRED",None))
async def go():
    app=Probe()
    async with app.run_test() as pilot:
        for ch in ["ф","й","о","л","р","д","е","ш","ы","к","у","ч","в","щ","Л","О","ю"]:
            try:
                await pilot.press(ch); await pilot.pause()
                print(f"  {ch!r} -> key={seen[-1][0]!r} char={seen[-1][1]!r}")
            except Exception as ex:
                print(f"  {ch!r} -> REJECTED: {type(ex).__name__}: {str(ex)[:70]}")
        print("\n  did the 'ф' binding fire an action?",
              any(s[0]=="ACTION FIRED" for s in seen))
asyncio.run(go())
