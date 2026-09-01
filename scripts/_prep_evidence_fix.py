from pathlib import Path
import re
import subprocess

# Keep source-contract assertions insensitive to Markdown wrapping.
path = Path("scripts/tests/test_commissioning_evidence_workflow.py")
text = path.read_text(encoding="utf-8")
text = text.replace(
    '        self.assertIn("without a `Finding` object", text)\n',
    '        self.assertIn("without a", text)\n        self.assertIn("`Finding` object", text)\n',
)
path.write_text(text, encoding="utf-8", newline="\n")

# CLAUDE.md intentionally snapshots committed state. Prep-carrier commits are
# real commits, so refresh the informational count from this exact carrier HEAD
# rather than widening the snapshot tolerance. The final self-clean commit moves
# it by one, which remains inside the existing bound.
claude = Path("CLAUDE.md")
page = claude.read_text(encoding="utf-8")
commits = int(subprocess.check_output(
    ["git", "rev-list", "--count", "HEAD"], text=True).strip())
updated, count = re.subn(
    r"(it now holds\n?)\s*\d+ commits,",
    lambda match: f"{match.group(1)}{commits} commits,",
    page,
    count=1,
)
if count != 1:
    raise SystemExit("CLAUDE.md current commit-count claim not found exactly once")
claude.write_text(updated, encoding="utf-8", newline="\n")
