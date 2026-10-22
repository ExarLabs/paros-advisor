"""Checks that the /paros command and the PAROS plugin stay one advisor.

Run: python tools/test_plugin.py   (no dependencies; exits non-zero on a failure)
For the full manifest check, also run `claude plugin validate .` where Claude Code is installed.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
failures = []


def check(cond, msg):
    if not cond:
        failures.append(msg)


plugin = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
market = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))

check(plugin.get("name") == "paros", "plugin.json: name must be 'paros' (users type /paros:paros)")
check("version" not in plugin, "plugin.json: no fixed version, so every commit reaches plugin users")
for a in plugin.get("agents", []):
    check((ROOT / a).is_file(), f"plugin.json: agent file missing: {a}")
check(len(plugin.get("agents", [])) == len(list((ROOT / "agents").glob("*/agent.claude.md"))),
      "plugin.json: every agents/*/agent.claude.md must be listed")
for s in plugin.get("skills", []):
    check((ROOT / s).is_dir(), f"plugin.json: skills folder missing: {s}")

entries = [p for p in market.get("plugins", []) if p.get("name") == "paros"]
check(len(entries) == 1, "marketplace.json: exactly one 'paros' entry")
if entries:
    e = entries[0]
    check(e.get("source") in ("./", "."), "marketplace.json: the plugin is the repository root")
    check(e.get("skills") == ["./install/plugin-skills/"],
          "marketplace.json: only the plugin skill loads, not the adoptable skills/ catalog")

check(not (ROOT / "bin").exists(), "no top-level bin/: Cowork refuses plugins that have one")

skill = (ROOT / "install/plugin-skills/paros/SKILL.md").read_text(encoding="utf-8")
command = (ROOT / "install/paros.command.md").read_text(encoding="utf-8")
check("name: paros" in skill, "plugin skill: frontmatter name must be paros")
for name, text in (("plugin skill", skill), ("/paros command", command)):
    check("install/ENTRY.md" in text, f"{name}: must hand over to install/ENTRY.md")
    check("$ARGUMENTS" in text, f"{name}: must pass the request on")
check("install.py" not in skill.split("No self-update")[0], "plugin skill: must not run the installer")
check((ROOT / "install/ENTRY.md").is_file(), "install/ENTRY.md missing")

for p in list(ROOT.glob("install/**/*.md")) + list(ROOT.glob(".claude-plugin/*.json")):
    check(chr(0x2014) not in p.read_text(encoding="utf-8"), f"no em dashes: {p.relative_to(ROOT)}")

if failures:
    print("FAIL")
    for f in failures:
        print(" -", f)
    sys.exit(1)
print("ok: the /paros command and the plugin share one entry")
