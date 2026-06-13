# ReasonRDN — The Shared Memory Substrate for the Agentic Era

**The easy, production-grade on-ramp to the full Astrognosy WARF / reason:// ecosystem.**

One memory layer that makes every agent dramatically more effective with persistent, high-signal context — while the proprietary Positional Correlation Fields (PCF) mathematics stay completely protected inside the astragnostic engine.

### How the real stack works (important)

- **Local / this package**: reason-ecosystem (what you're looking at). Local private node, unified client, handoffs, git sync, GUI, MCP, `rdn` CLI. Perfect for personal + operator use.
- **warf Xchange reference broker** (https://warf.astrognosy.com on Railway, Postgres lives here): The public front door for deposits, shares, and arbitration.
- **astragnostic-api** (AWS ECS): The domain-agnostic PCF engine (pride and joy). The broker forwards scoring here (service-to-service with secret).
- **Xport / reason:// registry** (https://reason.astrognosy.com): Where promoted, high-kappa artifacts land for easy public resolution by any agent.
- After Xchange + Xtend, winners promote to reason:// on the Xport.

When you do `install.py --xchange` or set `REASON_USE_XCHANGE=1`:
- Your handoffs and `remember` calls go to the warf Xchange broker (warf.astrognosy.com).
- The broker routes scoring to astragnostic-api (AWS).
- High-value results can promote to the reason:// Xport registry (reason.astrognosy.com).

This package is deliberately the **simple, safe, local + bridge** layer. The advanced non-invertible transfer and full engine live in the reference monowarfo/warf implementations and the reason_py SDK. Perfect separation for IP protection.

**Why this can be a 200k-star project:**
- Local-first and private by default
- **Immediately useful** to any coding agent with almost zero setup (tell your agent "install reason-ecosystem --xchange")
- Protected PCF fingerprints + reason:// addressing
- Seamless federation from personal memory to collective intelligence on the Xchange
- Works for human operators (GUI + CLI) and autonomous agents via MCP
- Turns every commit, insight, and decision into something any future agent (or human) in the network can resolve

The core IP (PCF math) is deliberately not exposed. You only ever see safe outputs (`structural_hash`, content, provenance-style metadata).

## Quick Start (agents or humans)

```powershell
# Standard (local private node + full power)
py -3.13 install.py

# Auto-deposit reasoning artifacts to the central warf Xchange
py -3.13 install.py --xchange
```

Tell any agent: **"install reason-ecosystem"** or **"install reason-ecosystem --xchange"**.

After install you get:
- The `rdn` CLI (`rdn remember`, `rdn recall`, `rdn --xchange status`, ...)
- MCP tools auto-registered for Claude Desktop / many other agents
- Easy local node or direct use of https://warf.astrognosy.com for ecosystem sharing
- Unified client that prefers the Xchange (or your node_url) with local SQLite mirror/fallback

See `install.py --help` and `rdn --help`. Set `REASON_USE_XCHANGE=1` anywhere for Xchange mode.

### Hero "Try Immediately" Path (cross-platform, reliable)

```powershell
pip install 'reason-rdn[full]' && rdn start
```

This is the primary, reliable way to "start using rdn". It gives you the full coherent harness experience instantly:
- The badass dashboard with live metrics (estimated token savings, velocity, ship rate, vibe stars)
- Workflow suggestions
- Xchange mode for feeding the collective (broker → astragnostic-api scoring → reason Xport)
- Full CLI, MCP tools, etc.

Tell any agent: **"install reason-rdn[full] and run rdn start"**.

See `install.py --help` and `rdn --help`. Set `REASON_USE_XCHANGE=1` for Xchange.

### Windows One-Stop .exe (secondary, simplified for reliability)

The .exe was for simplicity, but bundling the full dashboard is difficult (as seen in build warnings and connection issues). Per the plan, we simplified it.

Build:
```powershell
python -m pip install pyinstaller pystray Pillow
python package.py
# or py -3.13 install.py --build
```

Result: dist\rdn.exe and rdn-portable.zip

What the EXE delivers (double-click or `rdn.exe` / `rdn.exe start`):
- Excitement banner
- Auto-starts local private node (8765) unless XCHANGE mode
- System tray icon for control (Open Dashboard, Start/Restart Node, Start/Stop MCP for agents, Quit)
- Full CLI (rdn.exe remember "..." etc.)

For the full badass metrics dashboard (the "one stop" visual experience), use the hero pip path above (it runs the Streamlit UI reliably because Python is present).

The EXE is a solid Windows "download and run" channel for the node + CLI + tray, without the bundling complexity of the rich UI.

This respects the simplicity goal while keeping the EXE useful.

### Ports (to avoid confusion)
- Node (memory API / "reason db" backend): http://127.0.0.1:8765
- Dashboard (the rich UI/harness with metrics, suggestions, Xchange view): http://localhost:8501 (Streamlit default)

The dashboard is the visual "one stop" for the harness. The node is the API.

### Timeline Note
AI dev velocity is insane. We ship in weeks/sprints, not 12 months. The hero path and unblocked EXE are priority for "try immediately". Harness expansions (real token accounting, flywheel suggestions) follow quickly.

## Architecture at a Glance

```
Your agents / GUI / CLI / handoffs
          │
          ▼
Local private node  (this repo)  ──►  Local SQLite fallback
          │
          │  (when Xchange mode enabled)
          ▼
Railway Xchange Broker  (warf.astrognosy.com + Postgres)
          │
          │  service-to-service
          ▼
astragnostic-api (api.pcfic.com on AWS ECS)  ←── Grand master (PCF + Xtend scoring vs current placeholder + corpus)
          │   (serves WARF + Pacific workloads)
          ▼  (if good)
Xport / reason:// registry (reason.astrognosy.com + xport.astrognosy.com)  ←── Public canonical resolution
```

This repo = the delightful local + agent entry point that can feed the full engine.

The heavy PCF lifting and multi-implementation engine lives in astragnostic-api (never exposed in this public surface).

## The Broader Ecosystem (context from the full stack)

- **reason-ecosystem** (here): Easy install, local RDN, MCP, CLI, auto Xchange bridge.
- **warf/**: Public IP-safe mirror + docs of the Xchange reference.
- **monowarfo/**: Live reference node/broker implementation.
- **reason_py** (SDKs in warf/monowarfo): The advanced ReasonClient + WARFClient for full arbitration/xfer flows.
- **astragnostic-api** (api.pcfic.com on AWS ECS): The grand master engine. Runs PCF + Xtend (quality gate + promotion to canonical for a reason:// URI). Serves workloads for both WARF and Pacific products. The broker is the public proxy to it.
- Non-public branches: full non-invertible reasoning transfer (Xfer) and complete protocol.

Use this package for day-to-day. Point it at the Xchange when you want your reasoning to participate in the collective network.

## Architecture (simplified)

### **Three-layer system:**

```
┌─────────────────────────────────────────────────────┐
│  Operator (Desktop)         │  Agents (Claude/Grok) │
│  ReasonRDN GUI              │  warf-mcp tools       │
│  deposit/recall via GUI     │  remember/recall      │
└──────────────┬──────────────────────┬───────────────┘
               │                      │
               └──────────────┬───────┘
                              │
        ┌─────────────────────▼──────────────┐
        │  HTTP Memory API                   │
        │  /api/remember                     │
        │  /api/recall                       │
        │  /api/resolve                      │
        │  (rdn/node/server.py)              │
        └─────────────────────┬──────────────┘
                              │
        ┌─────────────────────▼──────────────┐
        │  Local SQLite DB                   │
        │  ~/.reason-rdn/private-node/       │
        │  warf-node.db                      │
        └───────────────────────────────────┘
```

### **Shared memory model:**

- **Single HTTP node** (local or remote) is the source of truth
- **Both operator and agents** talk to same node via HTTP
- **Content stored** in metadata_json (artifact_id, address, deposited_at, audit_hash)
- **Full audit chain** via address (reason://project/handoff/task-slug) and audit_hash

---

## User Guide

### **Operator Flow (ReasonRDN GUI)**

1. **Install:**
   ```powershell
   py -3.13 install_reason_ecosystem.py
   ```

2. **Start GUI:**
   ```
   dist\ReasonRDN.exe
   ```
   Or:
   ```powershell
   py -3.13 rdn\gui\app.py
   ```

3. **In the GUI:**
   - **Create Private Node** → Starts embedded HTTP server on localhost:8765 (auto-detected port)
   - **Install Hooks** → Installs git post-commit hooks in all discovered repos
   - **Deposit** → Manually push repo state to memory (tags: repo, branch, files)
   - **Recall** → Search all stored memories; query by keyword
   - **Stop Node** → Clean shutdown

### **Agent Flow (Claude/Grok via warf-mcp)**

1. **Install:**
   ```powershell
   py -3.13 install_reason_ecosystem.py --warf-only
   ```

2. **Use tools in Claude:**
   ```
   @use_mcp_tool reason-ecosystem remember
   content: "The ReasonRDN node is running on port 8765"
   tags: ["status", "infrastructure"]
   project: "astrognosy"
   ```

3. **Recall from memory:**
   ```
   @use_mcp_tool reason-ecosystem recall
   query: "ReasonRDN infrastructure"
   limit: 5
   ```

4. **Resolve specific artifact:**
   ```
   @use_mcp_tool reason-ecosystem resolve
   address: "reason://astrognosy/handoff/abc12345"
   ```

---

## Configuration

### **.reason-ecosystem.cfg** (auto-created at ~/.reason-ecosystem.cfg)

```json
{
  "version": "1.0",
  "node_url": "http://127.0.0.1:8765",
  "port": 8765,
  "private_storage": "C:\\Users\\<user>\\.reason-rdn\\private-node",
  "memory_db": "C:\\Users\\<user>\\.reason-rdn\\private-node\\warf-node.db",
  "mcp_enabled": true
}
```

### **Override node URL (for remote/shared):**

```powershell
py -3.13 install_reason_ecosystem.py --node-url https://my-shared-warf.railway.app
```

---

## One-Liner for Agents

**Simplest command for operators to share:**

```
py -3.13 install_reason_ecosystem.py --no-service
```

**For agents in Claude/Grok prompts:**

```
"install reason-ecosystem" → operator runs the above one-liner
```

**Result:** ReasonRDN + warf-mcp installed, shared memory ready, operator desktop running, agents can remember/recall.

---

## Files

| File | Purpose |
|------|---------|
| install_reason_ecosystem.py | Unified installer for both ReasonRDN + warf-mcp |
| RDN/rdn/node/server.py | Embedded HTTP memory node |
| RDN/rdn/gui/app.py | Desktop operator console |
| wharf/warf_ecosystem_client.py | HTTP client for memory API |
| wharf/warf_mcp_server.py | MCP server for Claude/Grok/Codex |
| ~/.reason-ecosystem.cfg | Unified config (auto-created) |

---

**Status:** ✅ Production-grade direction. IP-protected structural fingerprints, unified client, auto-discovery, secure-by-default node, excellent MCP surface, and a friendly `rdn` CLI.

The goal is to become the default memory layer that every serious agentic workflow uses.

## Quick Start (designed for agents too)

```powershell
# One line (human or agent)
py -3.13 install.py

# Or target the warf Xchange for ecosystem-wide sharing of reasoning artifacts:
py -3.13 install.py --xchange

# Tell any agent: "install reason-ecosystem" or "install reason-ecosystem --xchange"
```

After install:
- `rdn remember "Fixed the critical auth race" --tags security,pcf`
- `rdn recall "auth race"`
- `rdn --xchange recall "handoff"`   # explicitly hit the central Xchange
- `rdn status`
- Agents automatically get powerful `remember`/`recall`/`resolve` tools (registered in Claude Desktop, etc.)

To use the Xchange from code/agents without installer:
- Set `REASON_USE_XCHANGE=1` (or `REASON_NODE_URL=https://warf.astrognosy.com`)
- For authenticated Xchange access: also set `REASON_RDN_TOKEN=...`

See `install.py` for flags and `rdn --help`.
