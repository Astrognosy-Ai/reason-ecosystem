---
title: "The reason:// URI Scheme"
abbrev: "reason-uri"
docname: draft-reason-uri-00
category: info
submissiontype: IETF
number:
date:
consensus: false
v: 3
area: "Applications and Real-Time"
workgroup: ""
keyword: ["URI", "memory", "agents", "resolution"]
stand_alone: yes
pi: [toc, sortrefs, symrefs, compact, comments]
author:
  - name: Astrognosy Contributors
    organization: Astrognosy
    email: hello@astrognosy.com
---

# The reason:// URI Scheme

## Abstract

This document defines the `reason` URI scheme for addressing high-signal, addressable reasoning artifacts across local, federated, and public memory substrates. `reason://` URIs enable agents and humans to deposit, discover, and resolve persistent context that improves future reasoning without requiring re-inference from scratch.

## Introduction

Modern AI agents suffer from statelessness. Every new session often starts reasoning from zero even when high-quality prior work on the exact same problem exists. The `reason://` scheme provides a simple, globally usable naming system for artifacts that represent "the best known reasoning for this problem at this time."

A `reason://` address is intended to be:
- Stable and human-readable (like a path)
- Resolvable to a current best artifact (via Xport-style registries or local nodes)
- Suitable for both private local use and public federated Xchange networks
- Accompanied by safe, non-invertible structural fingerprints for correlation without leaking proprietary content

This document only defines the URI syntax and high-level semantics. Resolution mechanisms, artifact formats, and Xchange protocols are described in companion documents.

## Syntax

The general form is:

```
reason://<authority>/<path>
```

- `authority`: A logical namespace or project (e.g. `ops`, `infra`, `my-team`, `astrognosy`). Intended to be decentralized; there is no single central registry of authorities.
- `path`: A hierarchical, slash-separated identifier for a class of problem or decision (e.g. `ecs/failures`, `auth/race-conditions`, `decision-theory/expected-value`).

Examples:

```
reason://ops/ecs/failures
reason://infra/auth/race-detection
reason://research/pcf/positional-correlation
```

The scheme is case-insensitive in the scheme name. Authorities and path segments are case-sensitive by default (following common URI practice for paths).

No query or fragment components are required by this specification, but implementations may use them for resolution hints (e.g. `?version=canonical` or `#fingerprint=...`).

## Semantics

A `reason://` URI names a **logical artifact** — the current best-known high-signal reasoning or handoff for the identified problem.

Resolution of a `reason://` URI should return:
- The primary content (reasoning, code sketch, decision record, etc.)
- Structured metadata (tags, provenance, structural fingerprint / audit hash, deposited timestamps, source)
- Optionally, a confidence or "kappa" score from quality/promotion systems

`reason://` URIs are **not** content hashes. They are stable *names* that can point to successively better artifacts over time (via promotion in Xchange + quality systems).

## Resolution

Resolution can be performed against:
- A local private node (always available, works offline)
- A public Xport / reason:// registry (e.g. reason.astrognosy.com)
- Any other implementation that understands the scheme

When multiple sources are available, clients are encouraged to prefer the highest-quality promoted canonical (when the user has opted into Xchange participation).

## Security Considerations

- URIs themselves are public names. Do not put sensitive values in the path if the URI will be widely shared.
- The actual content behind a URI may be private or public depending on the node/Xchange policy.
- Structural fingerprints (local `_pcf`-style hashes) are deliberately non-invertible and safe to share for correlation without revealing original content.
- Resolution should be authenticated when accessing private artifacts.

## IANA Considerations

This document requests that IANA register the `reason` URI scheme in the "URI Schemes" registry.

Scheme name: reason

Status: Provisional (or as determined by IANA process)

Applications/protocols that use this scheme: Agent memory systems, reasoning substrates, RDN nodes, Xchange brokers, Xport registries.

Contact: Astrognosy (or designated editor)

## References

- RFC 3986 (Uniform Resource Identifier (URI): Generic Syntax)
- Related work on named information (ni:) URIs, info: URIs, and content-addressable systems.

---

*This is an early exploratory skeleton. It will evolve.*