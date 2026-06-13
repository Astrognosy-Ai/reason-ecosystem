# Reason Ecosystem - Consolidated Directory

**⚠️ OUTDATED — This file reflects a pre-refactor layout.**

The current structure (as of the SELECTIVE EXPANSION plan and rdn/ package) is:
- Root: `rdn/` (the coherent on-ramp package: client, reason.py harness/metrics, mcp, node, dash, handoff with IP-safe _pcf hardcode)
- `package.py` + `rdn_launcher.py` for the simplified EXE (CLI + local node + tray only)
- `CEO_PLAN_INTEGRATED.md` (living plan + architecture per WARF + reason:// IETF drafts)
- `README.md`, `bootstrap.py`, `install.py` (hero `pip install 'reason-rdn[full]' && rdn start`)
- `legacy-operator/` (explicitly deprecated, see its README and the plan)

See `CEO_PLAN_INTEGRATED.md`, `README.md`, and `rdn/` for the accurate current layout, role (local IP-safe on-ramp + bridge to external WARF network: broker → astragnostic Xchange + Xtend → reason:// Xport), and docs.

**Location:** `C:\Users\Scooter\Coworker\Projects\GitHub\Astrognosy\reason-ecosystem\`

(The historical text below is preserved for reference only.)

## Historical (Outdated) Directory Structure

(The structure below no longer matches the current `rdn/` package layout.)

```
reason-ecosystem/
├── install.py                          Main installer (unified)
├── setup.py                            Python package config
├── README.md                           Complete guide
│
├── operator/                           Desktop console (ReasonRDN)   [MOVED / legacy]
│   ├── gui/app.py                      customtkinter desktop UI
│   ├── node/server.py                  Embedded HTTP memory API
│   ├── handoff/sync.py                 Auto-deposit hooks
│   ├── network/client.py               HTTP memory client
│   ├── package.py                      PyInstaller build script
│   ├── tests/                          Test suite (9 tests)
│   └── README.md                       Operator docs
│
├── agent/                              Agent tools (warf-mcp)        [MOVED into rdn/mcp + rdn/client]
│   ├── warf_ecosystem_client.py        HTTP memory client
│   ├── warf_mcp_server.py              MCP server for Claude/Grok
│
├── core/                               Shared utilities (optional)
│   └── __init__.py
│
└── dist/
    └── ReasonRDN.exe                   Built desktop executable      [now rdn.exe via package.py]
```

See the note at the top of this file and `CEO_PLAN_INTEGRATED.md` / `README.md` for the current consolidated `rdn/` on-ramp structure.

## Quick Start

### Install Everything (Operator + Agent)

```powershell
cd reason-ecosystem
py -3.13 install.py
```

### Install Operator Only (Desktop)

```powershell
cd reason-ecosystem
py -3.13 install.py --operator-only
```

### Install Agent Only (Claude/Grok Tools)

```powershell
cd reason-ecosystem
py -3.13 install.py --agent-only --no-service
```

### Build EXE

```powershell
cd reason-ecosystem
py -3.13 install.py --build
```

## One-Liner for Operators

```powershell
cd C:\Users\Scooter\Coworker\Projects\GitHub\Astrognosy\reason-ecosystem
py -3.13 install.py --no-service
```

Then run:
```
dist\ReasonRDN.exe
```

## One-Liner for Agents

```powershell
cd C:\Users\Scooter\Coworker\Projects\GitHub\Astrognosy\reason-ecosystem
py -3.13 install.py --agent-only --no-service
```

## What Gets Created

**User home directory:**
- `~\.reason-ecosystem.cfg` — Unified config (node URL, port, storage path)
- `~\.reason-rdn\private-node\warf-node.db` — Shared memory database
- `~\.reason-rdn\private-node\private-node.port` — Node port discovery

**System:**
- `~/bin/rdn-sync.bat` — CLI shim for git hooks
- Task Scheduler: `ReasonRDN-Node` — Auto-start on login (optional)

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Operator GUI (operator/)  │  Agent Tools (agent/)  │
│  Desktop console           │  Claude/Grok MCP       │
│  Deposit/Recall via UI     │  Remember/Recall       │
└──────────────┬─────────────────────────┬────────────┘
               │                         │
               └────────────┬────────────┘
                            │
          ┌─────────────────▼──────────────┐
          │  HTTP Memory API               │
          │  /api/remember, /api/recall    │
          │  /api/resolve, /api/health     │
          │  (operator/node/server.py)     │
          └─────────────────┬──────────────┘
                            │
          ┌─────────────────▼──────────────┐
          │  SQLite Database               │
          │  ~/.reason-rdn/private-node/   │
          │  warf-node.db                  │
          └───────────────────────────────┘
```

## Files at a Glance

| Component | File | Purpose |
|-----------|------|---------|
| **Installer** | `install.py` | Single command to set up everything |
| **Operator GUI** | `operator/gui/app.py` | Desktop console |
| **Memory Node** | `operator/node/server.py` | HTTP endpoint for remember/recall/resolve |
| **Auto-deposit** | `operator/handoff/sync.py` | Git hooks that auto-deposit repo state |
| **HTTP Client** | `operator/network/client.py` | Internal HTTP client (used by GUI) |
| **Memory Client** | `agent/warf_ecosystem_client.py` | HTTP client for local/remote discovery |
| **MCP Server** | `agent/warf_mcp_server.py` | MCP tools for Claude, Grok, Codex |
| **Built EXE** | `dist/ReasonRDN.exe` | Executable for operators (no Python needed) |

## Usage Examples

### Operator: Deposit and recall via GUI

1. Run `dist\ReasonRDN.exe`
2. Click "Create Private Node"
3. Click "Install Hooks"
4. Click "Deposit" to save repo state
5. Click "Recall" to search memories

### Agent: Use Claude to remember and search

```
@use_mcp_tool reason-ecosystem remember
content: "Fixed critical bug in sync.py"
tags: ["bugfix", "high-priority"]
project: "astrognosy"

@use_mcp_tool reason-ecosystem recall
query: "critical bug"
limit: 10
```

## Deployment

### Local (Default)
- Operator runs private node on localhost:8765
- Each desktop has isolated memory
- Works offline

### Remote/Shared (Optional)
- Deploy `operator/node/server.py` to Railway, Docker, or cloud
- Point operator + agents at same URL via `--node-url` or `NODE_URL` env var
- Shared team memory

## Tests

```powershell
cd reason-ecosystem
py -3.13 -m pytest operator/tests -v
```

All 9 tests pass (sync, client, private node).

## Documentation

- **Main Guide:** `README.md` — Architecture, API, deployment
- **Operator Details:** `operator/README.md` — Desktop console
- **API Reference:** `README.md` — HTTP endpoints

---

**Status:** ✅ Consolidated, tested, ready to use/deploy.
