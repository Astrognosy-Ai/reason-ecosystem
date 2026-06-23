# ReasonRDN

**Local-first memory and reason:// handoffs for agents, developers, and teams.**

ReasonRDN gives agents durable context across sessions. It stores useful
handoffs locally, exposes them through a small Python/CLI/MCP surface, and can
optionally share selected artifacts through the public WARF broker.

```powershell
pip install 'reason-rdn[full]'
rdn start
```

## Why reason:// Exists

Agentic workflows lose time when every session has to rediscover the same
decisions, fixes, and operating context. `reason://` gives that work a stable
address.

- Deposit reusable context once.
- Resolve it later from the same agent, another agent, or a future session.
- Work locally by default.
- Opt in to network participation through the public broker when useful.

This repo is the public on-ramp. It includes the local node, client, CLI,
dashboard, MCP server, artifact metadata, and broker/Xport client paths. It does
not include private scoring, arbitration, ranking, or promotion internals.

## Quick Start

```bash
rdn remember "Fixed the critical auth race under load" --tags infra,auth
rdn recall "auth race"
rdn resolve "reason://infra/auth/race-detection"
rdn --xchange status
rdn list reason://infra
```

Python:

```python
import rdn as reason

reason.remember(
    "The canonical solution for this class of outage",
    tags=["infra", "outage", "ecs"],
    reason_address="reason://ops/ecs/failures",
)

artifact = reason.resolve("reason://ops/ecs/failures")
print(artifact)
```

## Features

- Local private node with SQLite fallback.
- CLI commands for remember, recall, resolve, prefix browsing, status, and start.
- MCP server so coding agents can remember and resolve project context.
- Streamlit dashboard for local memory, token savings, and reason:// browsing.
- Optional Xchange mode through `https://warf.astrognosy.com`.
- Xport resolution through `https://reason.astrognosy.com`.
- Simple artifact integrity metadata for local handoffs.

## Public Architecture

```text
Your code / CLI / Dashboard / MCP agents
        |
        v
Local ReasonRDN node
        |
        | optional Xchange mode
        v
Public WARF broker
https://warf.astrognosy.com
        |
        v
reason:// registry / Xport
https://reason.astrognosy.com
```

The broker is the public network boundary. This package does not expose the
private services or implementation details behind that boundary.

## Configuration

Turn on broker participation:

```bash
REASON_USE_XCHANGE=1 rdn start
```

Or for a single command:

```bash
rdn --xchange remember "Reusable deployment note" --project ops --tags ecs,deploy
```

Common environment variables:

- `REASON_USE_XCHANGE=1`: send selected operations to the public broker.
- `REASON_NODE_URL=...`: point at a local or remote compatible node.
- `REASON_RDN_TOKEN=...`: optional bearer token for authenticated deployments.

Local data lives under `~/.reason-rdn/`.

## IETF Context

The canonical public Internet-Draft records live on IETF Datatracker:

- [draft-westerbeck-reason-protocol](https://datatracker.ietf.org/doc/draft-westerbeck-reason-protocol/)
- [draft-westerbeck-warf-protocol](https://datatracker.ietf.org/doc/draft-westerbeck-warf-protocol/)
- [Jacob Westerbeck Datatracker profile](https://datatracker.ietf.org/person/jacob%40pcfic.com)

These are active Internet-Drafts, not RFCs. This repository links to the
official Datatracker records instead of carrying local draft text.

## Repository Layout

```text
rdn/
  client.py              Unified local/broker client
  reason.py              High-level Python API and harness metrics
  cli.py                 Command line interface
  dash.py                Dashboard
  handoff/
    fingerprint.py       Local artifact integrity hash helper
    protocol.py          Handoff deposit/resolve orchestration
    sync.py              Repository state sync helper
  mcp/
    server.py            MCP server for agent tools
  node/
    server.py            Local embedded memory node
examples/
  README.md              Usage examples
ietf-drafts/
  README.md              Official Datatracker links
```

## Development

```bash
pip install -e '.[full]'
py -3.13 -m pytest -q
```

## Public Boundary

ReasonRDN is intentionally public and thin. It owns local memory, reason://
client workflows, CLI/MCP/dashboard ergonomics, and optional broker routing.

It does not own private scoring engines, production promotion infrastructure,
model-control internals, sensing internals, or protected implementation details.

## License

Apache-2.0. See [LICENSE](./LICENSE).
