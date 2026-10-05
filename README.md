# Homework 12: säkerhetsutvärdering

Kör från detta repo på Windows 11:

```powershell
python run_evals.py
```

Köraren läser HW6:s `.codex/hooks.json` i syskonmappen `Git-safety-hook-demo`, väljer dess `commandWindows` för `PreToolUse` och skickar testfallen från `cases.json` till hooken via stdin. Testkommandona exekveras aldrig. En eller flera misslyckade kontroller ger exitkod 1. Om HW6 ligger på en annan plats används `--hw6-root SÖKVÄG`.
