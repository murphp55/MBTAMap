# MBTAMap — Agent Notes

## One-liner
Python project (planning phase) for visualizing real-time MBTA transit data and driving an ESP32 LED display.

## Run it
```
No reproducible build command identified.
```
No source files exist in the working tree yet — only README.md. Prerequisites per README: `python -m pip install requests matplotlib`.

## Where we are right now
- Last touched: 2025-09-22 (commit `9ea4c77 Update README.md`)
- Working on: Dormant — no recent activity. Only 2 commits total; repo currently contains only README.md.
- Known broken: Nothing known. There is no code to break. README has an uncommitted modification (`git status` shows ` M README.md`).

*This section goes stale fast. Check `git log -5` and `git status` before trusting it.*

## Gotchas
- The working tree has no `.py` files. README references `live_vehicle.py`, `station_map.py`, `red_line.py` as if removed during refactoring, but `git log --all` shows only 2 commits and neither contains those scripts. They do not exist in git history despite the README's claims — do not chase `git show <commit>:live_vehicle.py`.
- README's "Last Updated: April 2026" is aspirational/inaccurate; last actual commit is Sept 2025.
- MBTA API requires `x-api-key` header; no key management exists yet.

## Non-obvious conventions
Nothing unusual — standard Python patterns expected once code lands.

See README.md for project description, tech stack, and feature list.
