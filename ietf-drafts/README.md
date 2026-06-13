# IETF Drafts & Standardization Notes (Exploratory)

This directory contains early exploratory work toward potential IETF standardization of core ideas from the reason:// ecosystem.

**Current status:** These are **not** official IETF drafts. They are working notes and skeletons that capture the thinking behind addressable, high-signal, resolution-oriented memory artifacts.

## Goals (high level)

- Register `reason` as a URI scheme (or document it properly under an existing scheme if more appropriate).
- Describe the semantics of `reason://` addresses: stable, content-addressable (or provenance-addressable) references to high-value reasoning artifacts that can be resolved to the current best-known version.
- Define a minimal, extensible handoff / artifact metadata format suitable for both local persistence and federated Xchange networks.
- Outline security, privacy, and provenance considerations for agent-to-agent memory sharing.

## Files in this directory

- `draft-reason-uri-00.md` — Skeleton for "The reason:// URI Scheme".

Future drafts under consideration (not started):
- RDN Artifact and Handoff Format
- Xchange Arbitration Protocol considerations
- Resolution and Promotion semantics (Xport)

## How to contribute to these notes

These live in the public branch so the community (and future standards participants) can see the direction early. Feedback, issues, and pull requests that improve clarity, security considerations, or alignment with existing URI / linked-data work are very welcome.

When (and if) we decide to submit an actual IETF draft, we will follow the normal IETF process (individual or working group submission).

---

**Related public materials**

- The main README describes the practical `reason://` usage today.
- The `rdn` package and its `list_prefix`, `resolve`, and Xchange flows are the current reference implementation of the ideas.

We believe addressable memory is a missing primitive for the agentic web. Making the core ideas crisp and standardizable is part of the long-term mission.