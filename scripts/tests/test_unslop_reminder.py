"""Cases for the hook that puts the prose rules in front of every turn.

The hook exists because an instruction in a memory file did not fire. What these
press is the failure that would make it useless without anyone noticing: reading
the skill wrongly and injecting rules that say something other than what the skill
says.
"""

from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
HOOK = ROOT / ".claude" / "hooks" / "unslop_reminder.py"
SKILL = ROOT / ".claude" / "skills" / "unslop" / "SKILL.md"

sys.path.insert(0, str(HOOK.parent))
from unslop_reminder import pass_items, reminder  # noqa: E402


class Parsing(unittest.TestCase):
    """The steps are read from the skill, not restated in the hook."""

    def test_every_numbered_step_is_carried(self):
        items = pass_items(SKILL.read_text(encoding="utf-8"))
        self.assertEqual(9, len(items))

    def test_a_wrapped_step_arrives_whole(self):
        """Two steps wrap in the skill; a line-at-a-time read truncates them."""
        text = ("## Pass\n\n1. Keep it short.\n2. Treat abstract metaphor as suspect\n"
                "   unless it preserves a real distinction.\n\n## Next\n")
        self.assertEqual(
            ["Keep it short.",
             "Treat abstract metaphor as suspect unless it preserves a real distinction."],
            pass_items(text))

    def test_a_renamed_heading_yields_nothing_rather_than_a_stale_copy(self):
        self.assertEqual([], pass_items("## Steps\n\n1. Something.\n"))

    def test_no_steps_means_no_injection(self):
        """An empty read must stay silent; a hook that emits noise gets turned off."""
        run = subprocess.run([sys.executable, str(HOOK)], capture_output=True, text=True,
                             cwd=ROOT, timeout=30)
        self.assertEqual(0, run.returncode)


def configured_command() -> list[str]:
    """The exact argv the harness runs, read from settings rather than reconstructed."""
    settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
    entry = settings["hooks"]["UserPromptSubmit"][0]["hooks"][0]
    return [entry["command"], *entry["args"]]


class Emission(unittest.TestCase):
    """What lands in the window, run the way the harness runs it.

    These invoke the argv in `settings.json`, not the module. Testing the module
    passed while the configured command was `python -c unslop_reminder.py turn` -
    the bootstrap source had been replaced by the literal `-c` flag - so the hook
    raised NameError and emitted nothing on every turn, and nothing said so. A
    check that cannot see the thing it grades is the failure class `sov.md` names
    as this repository's most expensive.
    """

    def test_the_configured_command_emits_the_documented_shape(self):
        run = subprocess.run(configured_command(), capture_output=True, text=True,
                             cwd=ROOT, timeout=30, input="")
        self.assertEqual(0, run.returncode, run.stderr)
        payload = json.loads(run.stdout)
        self.assertEqual("UserPromptSubmit",
                         payload["hookSpecificOutput"]["hookEventName"])
        self.assertIn("unslop", payload["hookSpecificOutput"]["additionalContext"])

    def test_the_configured_command_works_from_a_subdirectory(self):
        """The bootstrap walks up to find .claude/hooks; a persisted cd must not break it."""
        run = subprocess.run(configured_command(), capture_output=True, text=True,
                             cwd=ROOT / "scripts", timeout=30, input="")
        self.assertEqual(0, run.returncode, run.stderr)
        self.assertIn("additionalContext", run.stdout)

    def test_the_configured_command_is_silent_outside_the_repository(self):
        """Nothing to find is not a failure: exit 0, emit nothing, never break a session."""
        run = subprocess.run(configured_command(), capture_output=True, text=True,
                             cwd=ROOT.parent, timeout=30, input="")
        self.assertEqual(0, run.returncode)
        self.assertEqual("", run.stdout.strip())

    def test_the_reminder_names_the_owning_skill(self):
        text = reminder(["Keep it short."])
        self.assertIn(".claude/skills/unslop/SKILL.md", text)


if __name__ == "__main__":
    unittest.main()
