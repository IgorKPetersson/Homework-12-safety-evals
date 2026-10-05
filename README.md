# Homework 12: Safety Evaluations

Run from this repository on Windows 11:

```powershell
python run_evals.py
```

The runner reads HW6's `.codex/hooks.json` from the sibling `Git-safety-hook-demo` directory, selects its `commandWindows` entry for `PreToolUse`, and sends each case in `cases.json` to the hook through stdin. It never executes the test commands. One or more failed checks produce exit code 1. If HW6 is elsewhere, use `--hw6-root PATH`.
