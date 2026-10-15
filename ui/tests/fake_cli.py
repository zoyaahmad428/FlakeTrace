"""FakeCli: stands in for `python -m runner` in ui/tests only (production code never imports it).

Usage: fake_cli.py <mode> diagnose --project P --victim V --n N --records DIR [--order FILE]
"""
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
F1_REPORT = REPO / "eval" / "reports" / "f1.json"


def main(argv):
    mode, args = argv[0], argv[1:]
    records = Path(args[args.index("--records") + 1])
    if mode == "report":
        shutil.copy(F1_REPORT, records / "run-x.report.json")
        print("FakeCli summary")
        return 0
    if mode == "args":
        (records / "args.json").write_text(json.dumps(args), encoding="utf-8")
        shutil.copy(F1_REPORT, records / "run-x.report.json")
        return 0
    if mode == "unicode-error":
        print("error: café ✓ failed", file=sys.stderr)
        return 1
    if mode == "sleep":
        time.sleep(30)
        return 0
    if mode == "spawn-sleep":
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
        (records / "child.pid").write_text(str(child.pid), encoding="utf-8")
        time.sleep(60)
        return 0
    raise SystemExit(f"FakeCli: unknown mode {mode}")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
