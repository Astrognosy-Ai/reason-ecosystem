# ReasonRDN (LEGACY / DEPRECATED)

**🚫 DO NOT USE — This entire directory is legacy code from pre-refactor iterations.**

The modern, coherent on-ramp is in the root `rdn/` package:
- `rdn/` (client, reason.py with HarnessMetrics + token accounting, mcp, node, dash, handoff/_pcf with IP-safe hardcoded fingerprints)
- Hero path: `pip install 'reason-rdn[full]' && rdn start`
- Simplified EXE (CLI + local node + tray only) via `package.py` + `rdn_launcher.py`
- Full alignment with external WARF network (broker → astragnostic Xchange + Xtend → reason:// Xport promotion)

See:
- `README.md` (architecture + quickstart)
- `CEO_PLAN_INTEGRATED.md` (living plan + GSTACK review)
- `rdn/` source + `bootstrap.py` / `install.py`

This directory is kept only for historical reference. It will be removed in a future cleanup. All new development, agents, and operators must use the `rdn` harness.

**Last updated during eng review + build pass (token wiring + first-run enhancements).**

---

ReasonRDN (historical)

ReasonRDN is a cross-agent memory layer for software teams. It captures local repo state, fingerprints it structurally, and deposits it as `reason://` artifacts that any agent can resolve later.

It is designed for practical multi-agent continuity across tools like Copilot, Claude, Cursor, and Gemini.

## (Historical content below — do not rely on any of this for current usage) 

## Why teams use it (historical)

- **Persistent context across tools:** handoffs survive agent/session boundaries.
- **Fast onboarding for each task:** resolve existing artifacts before reasoning from scratch.
- **Private-first operation:** target a private WARF node, with local DB fallback.
- **Automation included:** one-shot sync, interval sync, and git-hook triggers.

## Architecture

1. **Capture:** collect branch, HEAD, status, diff stats, recent commits, touched files/dirs.
2. **Fingerprint:** compute a structural fingerprint from state tokens.
3. **Deposit:** save to WARF node (`/api/remember`) or local `~/.warf/memory.db`.
4. **Resolve/Recall:** retrieve artifacts by project/tag/query (`/api/recall`, `reason://`).

## Quickstart

### 1. Install

```bash
pip install -e .
```

### 2. Point to a WARF node (recommended)

```bash
set RDN_NODE_URL=https://your-private-warf-node
```

If unset, ReasonRDN falls back to local SQLite memory.

### 3. Run repo sync

```bash
rdn-sync --install-hooks --once
rdn-sync
```

## Desktop console (Windows)

- Launch from source:
  - `py -3.13 rdn\gui\app.py`
- Or run bundled exe:
  - `dist\ReasonRDN.exe`

The desktop app includes:
- node URL + repo root + interval settings
- embedded private WARF node creation
- sync-once
- hook installation
- start/stop auto-sync
- live artifact manifest + heartbeat

### Private node mode

- Set a port and storage folder in the sidebar.
- Click **CREATE PRIVATE NODE**.
- ReasonRDN starts a localhost WARF node in the background and points sync at it.
- Click **STOP NODE** to shut it down.

## Python SDK

```python
from rdn.handoff.protocol import ReasonRDN

rdn = ReasonRDN(node_url="https://your-private-warf-node")
rdn.deposit_handoff(
    "my-project",
    "Implemented sync summary and hook safety",
    ["sync", "hooks", "summary", "safety"],
    tags=["handoff", "repo-state", "release"],
)
```

## Build the exe

```bash
py -3.13 package.py
```

Output: `dist\ReasonRDN.exe`

## Operational notes

- Private node deployment and operations guidance: `docs/operations.md`
- Default scan root: `C:\Users\Scooter\Coworker\Projects\GitHub`
- Default interval: 5 minutes
- Hook targets: `post-commit`, `post-checkout`, `post-merge`

## Development checks

```bash
py -3.13 -m pytest
npx tsc --noEmit
npx eslint . --quiet
```

## Roadmap

- Windows service/Task Scheduler mode for unattended auto-sync
- richer conflict surfacing in desktop UX
- semantic recall mode in GUI
