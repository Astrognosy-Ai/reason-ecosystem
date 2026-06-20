# reason-rdn: reason:// The Shared Memory Substrate for the Agentic Era

**Local-first coherent memory with seamless participation in the global reason:// network.**

One import. Persistent high-signal context for humans *and* agents. Safe local fingerprints. Real token savings. A beautiful dashboard. And a clean path to the public Xchange where the best artifacts rise to the top.

```powershell
pip install 'reason-rdn[full]' && rdn start
```

Tell any agent: **"install reason-rdn[full] and run rdn start"**.

---

## Why reason:// exists

Every serious agentic workflow eventually hits the same wall: agents are stateless. They re-invent, re-debug, and re-decide the same things over and over.

`reason://` gives you **addressable, high-signal memory**:

- Deposit once with a stable `reason://` address.
- Later (same agent, different agent, next month) resolve it and pick up where the best prior reasoning left off.
- Local by default. Federated when you want it. Public canonicals when the network promotes a winner.

This package (`rdn`) is the **open, production-grade on-ramp**, providing the delightful local layer + bridge that makes participating in (and benefiting from) the larger reason:// ecosystem trivial and rewarding.

The advanced mathematics (Positional Correlation Fields / PCF) are calculated cleanly and securely under the hood, yielding safe, useful outputs.

---

## Hero Quick Start

### The one command everyone should run

```powershell
pip install 'reason-rdn[full]' && rdn start
```

This gives you immediately:

- The full **harness dashboard** (metrics, deposit, resolve, prefix explorer)
- Real **token savings, velocity, ship rate, vibe stars**
- Workflow suggestions
- Xchange controls (feed the collective when you want)
- Full `rdn` CLI + MCP tools for agents

### CLI examples

```bash
rdn remember "Fixed the critical auth race under load" --tags infra,auth,pcf
rdn recall "auth race"
rdn resolve "reason://infra/auth/race-detection"
rdn --xchange status          # see your impact + the network
rdn list reason://infra       # browse everything under a prefix
```

### For agents (Claude, Grok, Cursor, etc.)

Agents get powerful tools automatically via MCP:

```python
import rdn as reason

reason.remember(
    "The canonical solution for this class of outage",
    tags=["infra", "outage", "ecs"],
    reason_address="reason://ops/ecs/failures"   # permanent prefix is handled for you
)

art = reason.resolve("reason://ops/ecs/failures")
print(art)
```

Just say in your agent prompt: *"Use the reason-rdn MCP tools to remember and resolve via reason:// URIs."*

---

## Features

- **Beautiful Streamlit harness dashboard**: metrics that actually mean something, tree-view prefix explorer, recent URIs with one-click copy, deposit forms with permanent `reason://` prefix, Xchange toggle.
- **First-class CLI** (`rdn`): remember, recall, resolve, list prefixes, status, xchange flows, start the harness.
- **MCP server**: agents get `remember`, `resolve`, `status`, harness metrics, etc. out of the box.
- **reason:// URIs + powerful browsing**: `list_prefix("reason://infra")` returns everything under it. The dashboard renders it as a beautiful collapsible tree.
- **Real token accounting**: pass `tokens_used` on remember and `tokens_saved` on resolve. See your personal velocity and savings from network winners.
- **Xchange mode** (opt-in): high-signal artifacts you create can flow to the public broker, get scored by the protected engine, and (if they win) become the canonical for that `reason://` URI on the Xport registry.
- **Local private node always works**: 8765 by default. Full offline capability + SQLite mirror. The dashboard lives at 8501.
- **One coherent Python surface**: `import rdn as reason`. Everything important is available at the top level.
- **Simplified Windows one-stop**: `package.py` produces `rdn.exe` + portable zip (CLI + local node + tray). The rich dashboard is the reliable pip path.

---

## Architecture (Public Reference Network)

```
Your code / CLI / Dashboard / Agents (MCP)
                  │
                  ▼
Local private node (this package, port 8765)
   • Always available
   • Local SQLite fallback/mirror
   • Safe structural fingerprints (_pcf)
                  │
                  │  (when Xchange enabled)
                  ▼
Public Xchange Broker  (warf.astrognosy.com)
                  │
                  │  service-to-service scoring
                  ▼
astragnostic-api (api.pcfic.com)   ← Protected PCF engine + Xtend promotion
                  │
                  │  (winners only)
                  ▼
Xport / reason:// Registry  (reason.astrognosy.com + xport.astrognosy.com)
                  │
                  └─► Public canonical resolution for any agent
```

**This repo = the open on-ramp.**  
The heavy protected engine and promotion logic live in the reference network. Your high-quality local artifacts can compete there when you flip on Xchange.

---

## The reason:// URI

This is the killer feature.

```text
reason://<authority>/<path>
```

Examples:

- `reason://ops/ecs/failures`
- `reason://infra/auth/race-detection`
- `reason://research/positional-correlation`

**Permanent prefix in the UI/CLI**: you never have to type `reason://` every time.

**Prefix browsing is first-class**: incomplete URIs bring back everything below them (both locally and from the network when Xchange is on). The dashboard shows a live tree with folders and copy buttons.

Once an artifact is promoted through Xchange + the quality gate, resolving the URI gives you the current best-known reasoning instead of forcing the agent to rediscover it.

---

## Token Economics & the Flywheel (IP-Safe)

When you use `tokens_used=...` on remember and see `tokens_saved=...` on resolve, you're seeing the flywheel in action:

1. You create a high-signal artifact and give it a precise `reason://` address.
2. You (optionally) share it via Xchange.
3. The network scores it. Strong artifacts get promoted.
4. Later, you or anyone else resolves the same URI and the system tells you how many tokens you *didn't* have to spend.

The dashboard surfaces **velocity**, **ship rate**, and **vibe stars** so the value is visible in seconds.

This is deliberately designed so that contributing high-quality memory is personally rewarding.

---

## Installation

### Recommended (cross-platform, full experience)

```powershell
pip install 'reason-rdn[full]'
rdn start
```

`[full]` pulls in the dashboard (streamlit + plotly) and MCP support.

### Windows "download and run" (simplified)

```powershell
python package.py
# produces dist/rdn.exe + rdn-portable.zip
```

The executable gives you the node + full CLI + system tray. For the rich metrics dashboard, use the pip path above.

### From source (development)

```bash
pip install -e '.[full]'
```

See `install.py` and `bootstrap.py` for one-liner bootstrap options.

---

## Xchange & Configuration

Turn on participation in the public network:

```bash
REASON_USE_XCHANGE=1 rdn start
# or
rdn --xchange remember "..." --reason-address "reason://my-project/..."
```

Key environment variables:

- `REASON_USE_XCHANGE=1`: default to the public warf broker
- `REASON_NODE_URL=...`: point at any node (local or remote)
- Token accounting is passed explicitly in the API (`tokens_used`, `tokens_saved`)

All data lives under `~/.reason-rdn/`.

---

## Toward IETF Standardization

We believe `reason://` addressing + structured high-signal memory artifacts are a missing primitive for the agentic internet.

Exploratory draft work lives in the [`ietf-drafts/`](./ietf-drafts) directory:

- `draft-reason-uri-00.md`: early skeleton for the URI scheme itself (syntax, semantics, resolution, security considerations, IANA registration path).

These are **not yet submitted** IETF drafts. They are public working notes so the direction is visible early and the community can help shape them.

If you're interested in URI schemes, provenance, or agent memory protocols, we would love your input.

---

## Vision

Inference should feel like resolution when the problem has been solved well before.

`reason-rdn` + the reason:// network is how we get there: one high-quality, addressable artifact at a time.

Local-first and private by default.  
Federated and public when you choose.  
Protected mathematics where it matters.  
Visible economics so humans and agents actually use it.

---

## Status & Roadmap

- ✅ Coherent top-level API (`import rdn as reason`)
- ✅ Real token accounting + HarnessMetrics (velocity, ship rate, vibe stars)
- ✅ Prefix browsing + tree explorer + recent URIs with copy
- ✅ Xchange bridge + public reference endpoints
- ✅ MCP server for agents
- ✅ Beautiful dashboard + polished CLI
- ✅ Simplified reliable Windows channel
- 🚀 IETF draft skeletons published (public branch)
- Ongoing: more flywheel-aware suggestions, richer provenance, broader agent integrations

**License:** MIT (see `LICENSE`)

This package is fully open-source and provides all core tools, engines, clients, and dashboards required for local and federated use.

## Repository Layout

Here is the file structure of the repository and how they map to the system:

```
├── ietf-drafts/               # IETF RFC Drafts for the reason:// URI protocol
│   ├── README.md              # Documentation for drafts
│   ├── draft-reason-uri-00.md # Draft proposal for the reason:// URI scheme
│   └── draft-westerbeck-reason-protocol-01.txt # Full protocol specification
│
├── rdn/                       # Core python package source code
│   ├── __init__.py            # Top-level API exports (import rdn as reason)
│   ├── cli.py                 # Command line interface commands (rdn recall/remember/resolve/start)
│   ├── client.py              # Unified RDN client with local SQLite and remote Node fallback
│   ├── reason.py              # Token accounting, statistics, and HarnessMetrics tracking
│   ├── dash.py                # Streamlit web-dashboard implementation
│   │
│   ├── handoff/               # Handoff and structural fingerprint (PCF) logic
│   │   ├── __init__.py
│   │   ├── _pcf.py            # Positional Correlation Fields (PCF) fingerprint engine
│   │   ├── engine.py          # Deprecation layer for old PCFEngine imports
│   │   ├── protocol.py        # High-level orchestrator for agent handoff operations
│   │   └── sync.py            # Codebase repository sync automation
│   │
│   ├── mcp/                   # Model Context Protocol (MCP) integrations
│   │   ├── __init__.py
│   │   └── server.py          # MCP server exposing memory tools to Grok, Claude, etc.
│   │
│   └── node/                  # Local embedded server implementations
│       ├── __init__.py
│       └── server.py          # Embedded private memory node (lightweight HTTP)
│
├── gui/                       # Desktop runtime graphical user interface
│   └── app.py                 # CustomTkinter-based desktop controller dashboard
│
├── tests/                     # Unit testing suites
│   └── test_coherent_memory.py # Coherent tests for memory client, server, and metrics
│
├── bootstrap.py               # Fast one-liner bootstrap installer
├── install.py                 # Multi-platform unified CLI project setup installer
├── package.py                 # PyInstaller packaging configuration script
├── rdn_launcher.py            # Windows .exe system tray launcher wrapper
├── pyproject.toml             # Python build, dependencies, and packaging metadata
└── README.md                  # Project overview and specifications
```

---

## Contributing

Issues and PRs are welcome on the public branch.

When opening issues, please include:
- `rdn --version`
- Whether you are using Xchange mode
- A minimal reproduction for bugs

For larger discussions about the URI scheme or protocol, the `ietf-drafts/` notes are the right place to start.

---

**The memory layer for the agentic web starts here.**

```powershell
pip install 'reason-rdn[full]' && rdn start
```

Then give your agents (and yourself) the superpower of actually remembering.