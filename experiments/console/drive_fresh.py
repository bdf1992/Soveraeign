"""Drive the fresh-node surfaces against a node that is genuinely empty.

The empty state cannot be proven against the seeded store, so this stands up its
own server on a throwaway store and drives that. Nothing here reads a page's own
claims: it clicks what a person clicks, reads what the DOM rendered, and checks
the journal through the API rather than through the page.

    python experiments/console/drive_fresh.py [--shots]

A page error of any kind fails the round. A surface that logs an exception while
looking correct in a screenshot has not been proven.
"""

from __future__ import annotations

from http.server import ThreadingHTTPServer
from pathlib import Path
import json
import shutil
import sys
import tempfile
import threading
import urllib.request

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
SHOTS = HERE / "shots"
PORT = 8788
BASE = f"http://127.0.0.1:{PORT}"

sys.path.insert(0, str(HERE))
import door  # noqa: E402
import serve  # noqa: E402


def start(store: Path) -> ThreadingHTTPServer:
    """Serve the same door over a throwaway store, so the real one is untouched."""
    door.STORE = store
    server = ThreadingHTTPServer(("127.0.0.1", PORT), serve.Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def entries() -> int:
    """The journal length, read through the API rather than off the page."""
    with urllib.request.urlopen(f"{BASE}/api/state?dry=1") as response:
        return json.load(response)["counts"]["entries"]


def empty(store: Path) -> None:
    if store.exists():
        shutil.rmtree(store)


class Round:
    """One driven page: its checks, its failures, its console."""

    def __init__(self, name: str, page, shots: bool):
        self.name, self.page, self.shots = name, page, shots
        self.failures: list[str] = []
        self.errors: list[str] = []
        # A refusal this script asks for is expected traffic, not a dirty console.
        self.expecting = False
        page.on("pageerror", lambda e: self.errors.append(f"pageerror: {e}"))
        page.on("console", lambda m: self.errors.append(f"console.{m.type}: {m.text}")
                if m.type in ("error", "warning") and not self.expecting else None)

    def check(self, label: str, condition: bool, detail: str = "") -> None:
        print(f"  {'ok  ' if condition else 'FAIL'}  {label}{'  ' + detail if detail else ''}")
        if not condition:
            self.failures.append(f"{label} {detail}")

    def shot(self, label: str) -> None:
        if self.shots:
            SHOTS.mkdir(exist_ok=True)
            self.page.screenshot(path=str(SHOTS / f"{self.name}-{label}.png"), full_page=True)


def drive_founding(page, shots: bool, store: Path) -> Round:
    """Direction A: five acts, each a real call, on a node with nothing in it."""
    print("\nfresh-a — the founding")
    empty(store)
    r = Round("fresh-a", page, shots)
    page.goto(f"{BASE}/fresh-a", wait_until="networkidle")
    page.wait_for_selector("#arrival.gone", timeout=8000)
    page.wait_for_timeout(700)
    r.shot("01-arrival")

    r.check("journal starts empty", entries() == 0, f"{entries()} entries")
    r.check("looking did not write", page.locator("#tally").inner_text() == "0")
    r.check("the grain covers the page", grain_covers(page))
    r.check("five acts rendered", page.locator(".act").count() == 5)
    r.check("only the first act is live", page.locator(".act.live").count() == 1)
    r.check("later acts say what they wait on",
            "waits on step 1" in page.locator("#act-grant .go").inner_text().lower())

    page.locator("#act-session .go").click()
    page.wait_for_selector("#act-session.done", timeout=6000)
    r.check("the session landed", entries() == 2, f"{entries()} entries")
    r.check("its receipt is shown", page.locator("#act-session .out.on").count() == 1)
    r.check("the next act unlocked", page.locator("#act-grant.live").count() == 1)
    r.shot("02-session")

    # The refusal is the point of the second plate: prove it is a real one.
    before = entries()
    r.expecting = True
    page.locator("#act-grant .aside").click()
    page.wait_for_selector("#act-grant .out.refused", timeout=6000)
    refusal = page.locator("#act-grant .out").inner_text()
    r.check("an ungranted act is refused", "NO_LIVE_GRANT" in refusal, refusal.split("\n")[0])
    # The Console Service writes a receipt for most refusals but not for an
    # authority one, so what the plate says has to match what the journal did.
    wrote = entries() > before
    r.check("what it says about the record matches the record",
            ("not written" in refusal) != wrote,
            "journal grew" if wrote else "journal unchanged")
    r.expecting = False
    r.shot("03-refusal")

    page.locator("#act-grant .go").click()
    page.wait_for_selector("#act-grant.done", timeout=6000)
    page.locator("#act-channel .go").click()
    page.wait_for_selector("#act-channel.done", timeout=6000)
    page.locator("#act-thread .go").click()
    page.wait_for_selector("#act-thread.done", timeout=6000)
    r.check("the thread act shows both its entries",
            "open-thread" in page.locator("#act-thread .out").inner_text()
            and "under grant" in page.locator("#act-thread .out").inner_text())
    r.shot("04-mid")

    page.locator("#act-post textarea").fill("This node exists to hold what we decide.")
    page.locator("#act-post .go").click()
    page.wait_for_selector("#founded.on", timeout=8000)
    r.check("the node reports as founded", page.evaluate("() => window.__fresh.founded"))
    # The top of the page used to go on saying nothing had happened here while the
    # spine beside it listed every entry the visitor had just written.
    lede = page.locator("#ah2").inner_text()
    r.check("the lede followed the journal", "Nothing has happened" not in lede, lede)
    r.check("refilling is no longer offered over a node with entries in it",
            page.locator("#instead").evaluate("n => getComputedStyle(n).display") == "none")
    # The tally counts up rather than snapping, so let it settle before reading it.
    page.wait_for_function("() => document.getElementById('tally').textContent === "
                           "String(window.__fresh.node.counts.entries)", timeout=4000)
    r.check("the journal grew to what the page says",
            entries() == int(page.locator("#tally").inner_text()),
            f"api {entries()} / page {page.locator('#tally').inner_text()}")
    r.check("the spine ticked every entry",
            page.locator("#ticks .tick").count() == entries(),
            f"{page.locator('#ticks .tick').count()} ticks / {entries()} entries")
    r.shot("05-founded")

    # A digest chip that cannot be pulled on is decoration.
    page.locator("#act-post .out .pull").first.click()
    page.wait_for_selector("#pull.shown", timeout=5000)
    # The panel opens before the fetch lands; wait for the entry, not the slide.
    page.wait_for_selector("#pullchain div", timeout=5000)
    chain = page.locator("#pullchain").inner_text()
    r.check("a digest pulls back to its entry", "follows" in chain and "position" in chain)
    r.shot("06-pull")
    page.keyboard.press("Escape")
    return r


def drive_door(page, shots: bool, store: Path) -> Round:
    """Direction C: the node introduces itself and offers two real ways in."""
    print("\nfresh-c — the door")
    empty(store)
    r = Round("fresh-c", page, shots)
    page.goto(f"{BASE}/fresh-c", wait_until="networkidle")
    page.wait_for_selector("#arrival.gone", timeout=8000)
    page.wait_for_timeout(700)
    r.shot("01-arrival")

    r.check("journal starts empty", entries() == 0, f"{entries()} entries")
    r.check("the grain covers the page", grain_covers(page))
    r.check("what it holds is folded from the read",
            page.locator("#holds .cell").count() == 5)
    r.check("every count reads zero",
            page.locator("#holds .cell.zero").count() == 5)
    r.check("two ways in, both gestures", page.locator(".gesture").count() == 2)

    listed = page.evaluate("() => window.__door.ops.operations.filter(o => o.callable_here).length")
    page.locator("#can summary").click()
    page.wait_for_timeout(250)
    r.check("the operation list is folded, not hardcoded",
            page.locator("#ops .op").count() == listed, f"{listed} callable")
    r.shot("02-operations")

    page.locator("#found").click()
    page.wait_for_selector("#run .enter", timeout=10000)
    r.check("founding wrote five entries", len(page.locator("#run .line").all()) == 5)
    r.check("the journal agrees", entries() >= 10, f"{entries()} entries")
    # Founding opens a thread but says nothing in it, so the posts cell stays at
    # zero and should. What must be true is that the plate re-read the node.
    r.check("the counts re-read the node after founding",
            page.locator("#holds .cell").first.locator(".v").inner_text() == str(entries()),
            page.locator("#holds .cell").first.locator(".v").inner_text() + " shown")
    r.check("the posts cell is honest about still being zero",
            page.locator("#holds .cell.zero").count() == 1)
    r.shot("03-founded")
    return r


def drive_console(page, shots: bool, store: Path) -> Round:
    """Direction B: the console itself, on a node with nothing in it."""
    print("\nv5 — the console, empty")
    empty(store)
    r = Round("fresh-b", page, shots)
    page.goto(f"{BASE}/v5", wait_until="networkidle")
    page.wait_for_selector("#arrival.gone", timeout=8000)
    page.wait_for_timeout(700)
    r.shot("01-empty")

    r.check("the shell assembled with no channels",
            page.locator("#app.in").count() == 1)
    # Opening the console used to write the two entries of its own session, so an
    # untouched node greeted you by reporting that something had happened.
    r.check("looking at the console did not write to it", entries() == 0,
            f"{entries()} entries")
    r.check("the counts on screen agree",
            page.locator("#void .counts .c").first.locator(".v").inner_text() == "0")
    r.check("the rail carries an open slot", page.locator(".dom.add.only").count() == 1)
    r.check("the empty pane states the node, not a blank",
            "Nothing has happened here" in page.locator("#void h2").inner_text())
    r.check("the answer bar is out of the way",
            page.locator("#act").evaluate("n => getComputedStyle(n).display") == "none")
    r.check("no control hands over a command",
            "python " not in page.locator("#void").inner_text()
            and "seed.py" not in page.locator("#void").inner_text())

    page.locator("#void .go").click()
    page.wait_for_selector(".dom:not(.add)", timeout=8000)
    page.wait_for_timeout(400)
    r.check("opening the first channel landed", entries() >= 4, f"{entries()} entries")
    r.check("the rail now carries it", page.locator(".dom").count() == 2)
    # The re-render must not throw away the receipt of the act that caused it.
    r.check("its receipt survived the re-render",
            "RECORDED" in page.locator("#void .out.on").inner_text())
    r.shot("02-first-channel")

    r.check("the empty channel asks for its first thread",
            "Open the first thread" in page.locator("#void h2").inner_text())
    page.locator("#void .go").click()
    page.wait_for_selector("#posts .nothing", timeout=8000)
    r.check("the empty thread says whose post would be first",
            "No posts in this thread yet" in page.locator("#posts .nothing").inner_text())
    r.check("the answer bar came back",
            page.locator("#act").evaluate("n => getComputedStyle(n).display") != "none")
    r.shot("03-first-thread")

    page.locator("#text").fill("First.")
    page.locator("#send").click()
    page.wait_for_selector("#receipt.on", timeout=8000)
    page.wait_for_timeout(400)
    r.check("the first post landed", page.locator("#posts .post").count() == 1)
    r.check("its receipt is shown", "COMMITTED" in page.locator("#receipt").inner_text())
    r.shot("04-first-post")

    # The one act on this door that destroys records must be asked for on purpose.
    r.expecting = True
    refused = page.evaluate("() => window.__sov.call('console.empty', {})")
    r.check("emptying the node without meaning it is refused",
            refused["payload"]["reason_code"] == "CONFIRMATION_REQUIRED",
            refused["payload"]["reason_code"])
    r.check("and nothing was dropped", entries() > 0, f"{entries()} entries")
    r.expecting = False
    return r


def grain_covers(page) -> bool:
    """The film grain is a full-bleed overlay or it is a rectangle in the corner."""
    box = page.locator("#grain").bounding_box()
    view = page.viewport_size
    return box["width"] >= view["width"] - 1 and box["height"] >= view["height"] - 1


def main() -> int:
    shots = "--shots" in sys.argv or True
    store = Path(tempfile.mkdtemp(prefix="sov-fresh-")) / "console"
    server = start(store)
    rounds = []
    try:
        with sync_playwright() as play:
            browser = play.chromium.launch(channel="chrome")
            for driver in (drive_founding, drive_door, drive_console):
                page = browser.new_page(viewport={"width": 1600, "height": 980},
                                        device_scale_factor=2)
                rounds.append(driver(page, shots, store))
                page.close()
            browser.close()
    finally:
        server.shutdown()
        shutil.rmtree(store.parent, ignore_errors=True)

    print()
    bad = 0
    for r in rounds:
        for error in r.errors:
            print(f"  DIRTY  {r.name}  {error}")
        if r.failures or r.errors:
            bad += 1
            print(f"  {r.name}: {len(r.failures)} failed, {len(r.errors)} console")
        else:
            print(f"  {r.name}: clean")
    print(f"\nshots: {SHOTS}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
