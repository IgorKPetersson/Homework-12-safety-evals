"""Run HW12 cases against the Windows PreToolUse command configured in HW6."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


HERE = Path(__file__).resolve().parent
DECISIONS = {"allow", "deny", "ask"}


def load_hook(hw6_root: Path) -> tuple[str, float]:
    config_path = hw6_root / ".codex" / "hooks.json"
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    matches = []
    for entry in config["hooks"]["PreToolUse"]:
        if not re.search(entry.get("matcher", ""), "Bash"):
            continue
        for hook in entry.get("hooks", []):
            if hook.get("type") == "command" and hook.get("commandWindows"):
                matches.append(hook)
    if len(matches) != 1:
        raise ValueError(f"Expected one Windows Bash PreToolUse hook, found {len(matches)}")
    hook = matches[0]
    return hook["commandWindows"], float(hook.get("timeout", 10))


def read_decision(stdout: str) -> tuple[str, str]:
    if not stdout.strip():
        return "allow", ""
    output = json.loads(stdout)
    specific = output["hookSpecificOutput"]
    if specific.get("hookEventName") != "PreToolUse":
        raise ValueError("hookEventName is not PreToolUse")
    decision = specific["permissionDecision"]
    if decision not in DECISIONS:
        raise ValueError(f"Unknown permissionDecision: {decision!r}")
    return decision, specific.get("permissionDecisionReason", "")


def run_case(case: dict[str, Any], command: str, hw6_root: Path, timeout: float) -> dict[str, Any]:
    payload = case["stdin"]
    stdin = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    start = time.perf_counter()
    try:
        process = subprocess.run(
            command,
            input=stdin,
            text=True,
            capture_output=True,
            cwd=hw6_root,
            shell=True,
            timeout=timeout,
            check=False,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        decision, reason = read_decision(process.stdout)
        expected = case["expected"]
        errors = []
        if process.returncode != 0:
            errors.append(f"exit code {process.returncode}; stderr={process.stderr.strip()!r}")
        if decision != expected["decision"]:
            errors.append(f"expected {expected['decision']}, got {decision}")
        if expected.get("reason_nonempty") and not isinstance(reason, str):
            errors.append("reason is not a string")
        elif expected.get("reason_nonempty") and not reason.strip():
            errors.append("deny reason is empty")
        limit = expected.get("max_duration_ms")
        if limit is not None and elapsed_ms >= limit:
            errors.append(f"{elapsed_ms:.1f} ms exceeds {limit} ms")
        return {"id": case["id"], "passed": not errors, "decision": decision,
                "elapsed_ms": elapsed_ms, "errors": errors}
    except (subprocess.TimeoutExpired, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {"id": case["id"], "passed": False, "decision": "error",
                "elapsed_ms": elapsed_ms, "errors": [str(exc)]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hw6-root", type=Path, default=HERE.parent / "Git-safety-hook-demo")
    args = parser.parse_args()
    hw6_root = args.hw6_root.resolve()
    try:
        cases = json.loads((HERE / "cases.json").read_text(encoding="utf-8"))
        command, timeout = load_hook(hw6_root)
        if not isinstance(cases, list) or not cases:
            raise ValueError("cases.json must contain a nonempty list")
        for case in cases:
            expected = case["expected"]
            if expected["decision"] not in DECISIONS:
                raise ValueError(f"Invalid expected decision in {case['id']}")
        results = [run_case(case, command, hw6_root, timeout) for case in cases]
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        print(f"Setup error: {exc}", file=sys.stderr)
        return 2

    print(f"HW6 config: {hw6_root / '.codex' / 'hooks.json'}")
    print(f"Windows PreToolUse command: {command}")
    print(f"{'CASE':<28} {'RESULT':<7} {'DECISION':<9} {'TIME (ms)':>10}  DETAILS")
    print("-" * 85)
    for result in results:
        detail = "; ".join(result["errors"])
        print(f"{result['id']:<28} {'PASS' if result['passed'] else 'FAIL':<7} "
              f"{result['decision']:<9} {result['elapsed_ms']:>10.1f}  {detail}")
    passed = sum(result["passed"] for result in results)
    failed = len(results) - passed
    print(f"Total: {len(results)}  Pass: {passed}  Fail: {failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
