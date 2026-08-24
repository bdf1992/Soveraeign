"""Drive a freeze in a real browser and prove it works, element by element.

Nothing here reads the page's own claims. It clicks what a person clicks, reads
what the DOM actually renders, and checks the journal grew by the entries the act
should have written. A dirty console is a failed round: any page error at all
fails the run rather than being noted and passed over.

    python experiments/console/drive.py v1 [--shots]
"""

from __future__ import annotations

from pathlib import Path
import json
import sys
import urllib.request

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
SHOTS = HERE / "shots"
BASE = "http://127.0.0.1:8787"


def journal_length() -> int:
    """Read the journal through the API, not through the page."""
    with urllib.request.urlopen(f"{BASE}/api/state") as response:
        return json.load(response)["counts"]["entries"]


def drive(version: str, shots: bool = True) -> int:
    SHOTS.mkdir(exist_ok=True)
    failures: list[str] = []
    errors: list[str] = []

    with sync_playwright() as play:
        browser = play.chromium.launch(channel="chrome")
        page = browser.new_page(viewport={"width": 1600, "height": 980},
                                device_scale_factor=2)
        # A refusal this script asks for is expected traffic, not a dirty console.
        expecting_refusal = {"now": False}
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}")
                if m.type in ("error", "warning") and not expecting_refusal["now"] else None)

        def check(name: str, condition: bool, detail: str = "") -> None:
            print(f"  {'ok  ' if condition else 'FAIL'}  {name}{'  ' + detail if detail else ''}")
            if not condition:
                failures.append(f"{name} {detail}")

        def shot(name: str) -> None:
            if shots:
                page.screenshot(path=str(SHOTS / f"{version}-{name}.png"))

        page.goto(f"{BASE}/{version}", wait_until="networkidle")
        # Wait for the arrival to finish rather than photographing it mid-fade.
        try:
            page.wait_for_selector("#arrival.gone", timeout=6000)
        except Exception:
            pass
        page.wait_for_timeout(900)
        shot("01-arrival")

        state = page.evaluate("() => window.__sov && window.__sov.state")
        check("drive handle exposes state", bool(state))
        check("channels rendered", page.locator("#rail .dom").count() >= 10,
              f"{page.locator('#rail .dom').count()} channels")
        check("threads listed", page.locator("#threads .th").count() > 0,
              f"{page.locator('#threads .th').count()} threads")
        check("posts rendered", page.locator("#posts .post").count() > 0,
              f"{page.locator('#posts .post').count()} posts")
        check("post bodies carry text",
              len(page.locator("#posts .body").first.inner_text()) > 80)
        check("provenance shown on every post",
              page.locator("#posts .prov").count() == page.locator("#posts .post").count())

        waiting = page.evaluate("() => window.__sov.waiting")
        check("judgement queue is not empty", bool(waiting), f"{len(waiting or [])} unanswered")

        # Element-level pass: every channel opens and renders a thread.
        empty = []
        for index in range(page.locator("#rail .dom").count()):
            page.locator("#rail .dom").nth(index).click()
            page.wait_for_timeout(90)
            if page.locator("#posts .post").count() == 0:
                empty.append(page.locator("#colhead h2").inner_text())
        check("every channel opens onto posts", not empty, ", ".join(empty))

        # Open a decision that is genuinely unanswered, not just the first row.
        page.evaluate("""() => {
            const first = window.__sov.waiting[0];
            const t = window.__sov.state.threads.find(x => x.title === first);
            document.querySelectorAll('#rail .dom')[0].click();
            window.__sov.open(t.thread_id); }""")
        page.wait_for_timeout(200)
        shot("02-queue")

        before = journal_length()
        # Where the surface asks for an owner action first, give it one. A freeze
        # that demands a verb and a freeze that does not are both driven here.
        verbs = page.locator("#verbs .verb")
        if verbs.count():
            check("owner actions offered", verbs.count() == 4, f"{verbs.count()} verbs")
            verbs.first.click()
            page.wait_for_timeout(120)
            check("the chosen action is held", bool(page.evaluate("() => window.__sov.verb")))
        page.fill("#text", "Driven by drive.py: this answer was typed into the surface.")
        page.click("#send")
        page.wait_for_timeout(900)
        after = journal_length()

        check("posting wrote two journal entries", after == before + 2,
              f"{before} -> {after}")
        check("receipt is shown", page.locator("#receipt.on").count() == 1)
        receipt = page.locator("#receipt").inner_text() if page.locator("#receipt.on").count() else ""
        check("receipt says COMMITTED", "COMMITTED" in receipt, receipt[:70])
        check("the answer is in the thread",
              "Driven by drive.py" in page.locator("#posts").inner_text())
        if verbs.count():
            check("the recorded answer carries the owner action",
                  "ACCEPT" in page.locator("#posts").inner_text())
        check("the thread left the unanswered queue",
              len(page.evaluate("() => window.__sov.waiting")) == len(waiting) - 1)
        shot("03-answered")

        # A refusal must be visible, not swallowed. Post into a session that is closed.
        closed = page.evaluate("""() => {
            const s = window.__sov.state.sessions.find(x => x.lifecycle === 'CLOSED');
            return s ? s.session_id : null; }""")
        if closed:
            expecting_refusal["now"] = True
            refusal = page.evaluate("""async (sid) => {
                const t = window.__sov.thread;
                return await window.__sov.call('console.post',
                    { session_id: sid, thread_id: t, body: 'should refuse' }); }""", closed)
            check("a closed session is refused", refusal["status"] == 409,
                  str(refusal["payload"].get("reason_code")))
            check("the refusal carries a reason code",
                  bool(refusal["payload"].get("reason_code")))
            check("the refusal names its receipt",
                  bool((refusal["payload"].get("receipt") or {}).get("reason_code")))
            expecting_refusal["now"] = False

        # The operation console must run, not merely list. Open a row and drive it.
        rows = page.locator("#side details.op")
        if rows.count():
            check("operations render as controls", rows.count() >= 8, f"{rows.count()} rows")
            grant = page.locator("#side details.op", has_text="grant").last
            grant.locator("summary").click()
            page.wait_for_timeout(150)
            filled = grant.locator(".field.filled").count()
            check("context prefills what it knows", filled >= 1, f"{filled} prefilled")
            boxes = grant.locator(".field input")
            boxes.nth(1).fill("post")
            boxes.nth(2).fill("scope-from-the-surface")
            before_grant = journal_length()
            grant.locator(".run").click()
            page.wait_for_timeout(900)
            check("running an operation writes to the journal",
                  journal_length() == before_grant + 2,
                  f"{before_grant} -> {journal_length()}")
            check("the run shows its receipt",
                  "COMMITTED" in grant.locator(".out").inner_text(),
                  grant.locator(".out").inner_text()[:60].replace(chr(10), " "))
            shot("04-operations")

        # A settled decision must keep the verdict, and provenance must pull.
        if page.locator("#pull").count():
            verdicts = page.evaluate("() => window.__sov.verdicts")
            recorded = [k for k, v in (verdicts or {}).items() if v]
            check("an answered decision keeps its verdict", bool(recorded),
                  ", ".join(f"{k[:28]}={verdicts[k]}" for k in recorded[:2]))
            check("the verdict is on screen",
                  page.locator("#threads .verdict").count() > 0,
                  f"{page.locator('#threads .verdict').count()} shown")
            page.locator("#posts .prov span.pull").first.click()
            page.wait_for_timeout(700)
            check("the provenance pull-out opens", page.locator("#pull.out").count() == 1)
            chain = page.locator("#pullchain").inner_text()
            check("it resolves to a real journal entry", "entry_" in chain,
                  chain.split(chr(10))[0][:50])
            check("it names what the entry follows", "follows" in chain)
            shot("05-provenance")
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            check("escape closes it", page.locator("#pull.out").count() == 0)

        check("console stayed clean", not errors, "; ".join(errors[:3]))
        browser.close()

    print(f"\n{len(failures)} failing checks" if failures else "\nall checks pass")
    if shots:
        print(f"shots: {SHOTS}")
    return 1 if failures else 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    raise SystemExit(drive(args[0] if args else "v1", "--no-shots" not in sys.argv))
