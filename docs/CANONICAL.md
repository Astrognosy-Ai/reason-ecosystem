# ReasonRDN Canonical Note

ReasonRDN is the public on-ramp for reason:// memory, local-first agent context, and deterministic arbitration workflows.

## Owns

- Local private memory node.
- CLI, Python package, dashboard, and MCP tools.
- reason:// addressing and prefix browsing.
- Public bridge into Xchange/Reason workflows.
- Local artifact integrity metadata.
- Public implementation path aligned with active Datatracker Internet-Drafts.

## Does Not Own

- Protected scoring or promotion internals.
- Current Railway broker/Xport deployment lineage; that is `monowarfo`.
- Refinery or GnoSys implementation internals.

## Test Command

```powershell
py -3.13 -m pytest -q
```

## Public Boundary

This repo is intentionally public and thin. It may describe the architecture and provide client tools, but it must not absorb protected scoring, model-control, or sensing internals from private repos.

## IETF Context

The related active Internet-Drafts are:

- https://datatracker.ietf.org/doc/draft-westerbeck-reason-protocol/
- https://datatracker.ietf.org/doc/draft-westerbeck-warf-protocol/
- https://datatracker.ietf.org/person/jacob%40pcfic.com

Use "active Internet-Draft" or "IETF-track protocol work" language. Do not imply RFC approval.
