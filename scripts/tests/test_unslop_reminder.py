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


class Emission(unittest.TestCase):
    """What lands in the window."""

    def test_the_payload_is_the_documented_shape(self):
        run = subprocess.run([sys.executable, str(HOOK)], capture_output=True, text=True,
                             cwd=ROOT, timeout=30)
        payload = json.loads(run.stdout)
        self.assertEqual("UserPromptSubmit",
                         payload["hookSpecificOutput"]["hookEventName"])
        self.assertIn("additionalContext", payload["hookSpecificOutput"])

    def test_the_reminder_names_the_owning_skill(self):
        text = reminder(["Keep it short."])
        self.assertIn(".claude/skills/unslop/SKILL.md", text)

    def test_the_hook_is_registered_for_every_turn(self):
        settings = json.loads((ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))
        registered = json.dumps(settings["hooks"]["UserPromptSubmit"])
        self.assertIn("unslop_reminder.py", registered)


if __name__ == "__main__":
    unittest.main()
