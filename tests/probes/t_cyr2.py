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
from textual.widgets import Input, Static
from textual.binding import Binding
fired=[]
class Probe(App):
    BINDINGS=[Binding("a,ф","boom","Add"), Binding("e,у","boom2","Rename")]
    def compose(self)->ComposeResult:
        yield Input(id="inp"); yield Static("x")
    def action_boom(self): fired.append("add")
    def action_boom2(self): fired.append("rename")
async def go():
    app=Probe()
    async with app.run_test() as pilot:
        inp=app.query_one(Input); inp.focus(); await pilot.pause()
        # type a Russian phrase containing bound letters ф and у
        for ch in "фуфайка":
            await pilot.press(ch)
        await pilot.pause()
        print(f"  typed 'фуфайка' into a focused Input")
        print(f"    Input value : {inp.value!r}")
        print(f"    actions fired: {fired}")
        print(f"    -> the focused Input {'KEPT' if inp.value=='фуфайка' else 'LOST'} the characters")
        # and the ASCII equivalent, for comparison
        inp.value=""; fired.clear()
        for ch in "aede":
            await pilot.press(ch)
        await pilot.pause()
        print(f"  typed 'aede' into a focused Input")
        print(f"    Input value : {inp.value!r}   actions fired: {fired}")
        # now blur the input -- the bindings should fire
        inp.blur(); app.set_focus(None); await pilot.pause()
        fired.clear()
        await pilot.press("ф"); await pilot.press("у"); await pilot.pause()
        print(f"  with nothing focused, ф and у fired: {fired}")
asyncio.run(go())
