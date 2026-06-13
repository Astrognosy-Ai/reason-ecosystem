# ReasonRDN + warf Xchange Examples

This directory shows how to use reason-ecosystem for local memory + seamless auto-deposit to the full stack.

**Important architecture note** (from the real system):
- Deposits with Xchange mode go to the Railway reference **broker** (warf.astrognosy.com).
- The broker forwards actual scoring to **astragnostic-api** (AWS ECS) — the domain-agnostic PCF engine.
- High-value results can be promoted to the reason:// **Xport** registry at reason.astrognosy.com.

All examples keep the PCF math protected (only safe fingerprints + content are ever sent from here). The real engine lives in astragnostic-api.

## Quick Agent Prompts (copy-paste these to any coding assistant)

"Install and configure reason-ecosystem with auto-deposit to the warf Xchange so my reasoning artifacts are available ecosystem-wide."

"Use the rdn CLI or MCP tools to remember this solution under reason://ops/deployment/ecs-task-failures and share it to the Xchange."

"Before solving this, resolve reason://<domain>/<category>/<task> from the Xchange to see if a verified artifact already exists."

## Python Examples

### 1. Basic local + Xchange deposit (auto when configured)

```python
from rdn.handoff import ReasonRDN
from rdn.client import XCHANGE_URL, RDNClient

# Local-first (default)
rdn = ReasonRDN()
rdn.deposit_handoff(
    project="my-team",
    summary="ECS tasks need assignPublicIp: ENABLED for ECR pulls in private subnets",
    state_tokens=["ecs", "ecr", "private-subnet", "assignPublicIp"],
    tags=["infra", "ecs", "networking"]
)

# Explicit Xchange (or set REASON_USE_XCHANGE=1 / use --xchange in CLI)
xchange = RDNClient(node_url=XCHANGE_URL)
result = xchange.share_to_xchange(
    content="The definitive fix for private ECR pull failures on Fargate",
    uri="reason://ops/ecr/private-pull-failures",
    tags=["production", "ecs", "ecr"],
    project="ops"
)
print("Shared to Xchange:", result)
```

### 2. Resolve from Xchange (reason:// style)

```python
from rdn.client import RDNClient, XCHANGE_URL

client = RDNClient(node_url=XCHANGE_URL)

# Our simple resolve still works
artifact = client.resolve("reason://ops/ecr/private-pull-failures")

# Or the advanced Xport-style if the node supports full reason:// artifacts
advanced = client.resolve_reason_uri("reason://ops/ecr/private-pull-failures")
if advanced:
    print("Score / provenance available:", advanced.get("score") or advanced.get("structural_hash"))
```

### 3. Auto from git sync / handoff (production workflow)

Run with the Xchange configured:

```bash
REASON_USE_XCHANGE=1 rdn-sync --once --install-hooks
```

Or in code:

```python
from rdn.handoff.sync import run_once
run_once(None, root="/path/to/monorepo", node_url="https://warf.astrognosy.com", install_repo_hooks=True)
```

Every commit now contributes a rich, fingerprinted handoff that can be resolved by any agent in the ecosystem.

## MCP / Agent Tools (after install)

Once `pip install -e ".[mcp]"` or via the installer, agents get:

- `remember` / `recall` / `resolve` (local or Xchange depending on config)
- With `--xchange` or env, everything federates.

See the main README for Claude Desktop / Cursor registration.

## Security Notes (Production)

- Local node: always localhost-only by default.
- Xchange: use `REASON_RDN_TOKEN` (or `WARF_API_KEY`) for authenticated access to the live node.
- All deposits carry `structural_hash` (protected PCF output) + audit information for integrity.

## Next-Level (full WARF ecosystem)

This package is the easy on-ramp. For the complete non-public features (full arbitration, Xtend quality gate, Xfer non-invertible transfer, advanced reason:// patterns with thresholds), see the warf/monowarfo reference implementations and the reason_py SDK.

The public surface here is deliberately IP-safe while still extremely powerful for day-to-day agent memory and handoff.

---

Run `rdn --help` and `rdn --xchange status` after install to explore.
