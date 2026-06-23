# ReasonRDN Examples

This directory shows how to use ReasonRDN for local memory and optional
broker-backed reason:// workflows.

## Architecture Note

- Local memory works without network access.
- Xchange mode sends selected artifacts to `https://warf.astrognosy.com`.
- The broker is the public boundary for network workflows.
- Public registry resolution uses `https://reason.astrognosy.com`.

Private scoring and promotion internals are not part of this repository.

## Agent Prompts

```text
Install ReasonRDN and use the rdn CLI or MCP tools to remember durable project context.
```

```text
Before solving this, resolve reason://<domain>/<category>/<task> to see whether useful prior context exists.
```

```text
Remember this solution under reason://ops/deployment/ecs-task-failures with tags ops,ecs,networking.
```

## Local Deposit

```python
from rdn.handoff import ReasonRDN

rdn = ReasonRDN()
rdn.deposit_handoff(
    project="my-team",
    summary="ECS tasks need assignPublicIp: ENABLED for ECR pulls in private subnets",
    state_tokens=["ecs", "ecr", "private-subnet", "assignPublicIp"],
    tags=["infra", "ecs", "networking"],
)
```

## Share Through The Broker

```python
from rdn.client import XCHANGE_URL, RDNClient

client = RDNClient(node_url=XCHANGE_URL)
result = client.share_to_xchange(
    content="The fix for private ECR pull failures on Fargate",
    uri="reason://ops/ecr/private-pull-failures",
    tags=["production", "ecs", "ecr"],
    project="ops",
)
print(result)
```

## Resolve A reason:// URI

```python
from rdn.client import RDNClient, XCHANGE_URL

client = RDNClient(node_url=XCHANGE_URL)
artifact = client.resolve_reason_uri("reason://ops/ecr/private-pull-failures")
print(artifact)
```

## CLI

```bash
rdn remember "Useful deployment note" --project ops --tags deploy,ecs
rdn recall "deployment note" --project ops
REASON_USE_XCHANGE=1 rdn-sync --once --install-hooks
```

## Security Notes

- The local node is localhost-only by default.
- Use `REASON_RDN_TOKEN` or `WARF_API_KEY` for authenticated deployments.
- This public package contains client and local-memory code only.
