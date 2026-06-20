"""
rdn — friendly CLI for the ReasonRDN memory substrate.

Designed to be useful both for humans and for agents that can shell out.

Examples:
    rdn remember "Fixed the critical race in the handoff protocol" --tags infra,bugfix
    rdn recall "race condition" --project ReasonRDN --limit 5
    rdn resolve reason://ReasonRDN/handoff/abc12345
    rdn status
"""

from __future__ import annotations

import argparse
import json
import sys

from rdn.handoff import ReasonRDN
from rdn.client import RDNClient, XCHANGE_URL, XCHANGE_BROKER_URL, XPORT_URL, REASON_XPORT_URL
from rdn import __version__
import os  # for env fallback for tokens


def _resolve_node_url(args) -> Optional[str]:
    """Helper to pick node: explicit --node > --xchange (warf Xchange broker) > args.node"""
    if args.xchange:
        return XCHANGE_BROKER_URL  # broker (warf.astrognosy.com) by default — scoring goes to astragnostic-api
    return getattr(args, "node", None)


def cmd_remember(args):
    node_url = _resolve_node_url(args)
    rdn = ReasonRDN(node_url=node_url)
    tags = args.tags.split(",") if args.tags else None
    res = rdn.deposit_handoff(
        project=args.project,
        summary=args.content,
        state_tokens=(args.tokens or "").split() if args.tokens else [args.content[:30]],
        tags=tags,
    )
    # Real token accounting: use public record helper (avoids double-deposit while ensuring
    # HarnessMetrics gets the tokens_used for accurate savings/velocity/ship-rate).
    tokens_used = getattr(args, "tokens_used", None) or os.environ.get("RDN_TOKENS_USED")
    if tokens_used:
        try:
            import rdn as reason
            reason.record_handoff(args.content, tags, tokens_used=int(tokens_used))
        except Exception:
            pass
    print(json.dumps(res, indent=2))


def cmd_recall(args):
    node_url = _resolve_node_url(args)
    client = RDNClient(node_url=node_url)
    results = client.recall(
        query=args.query,
        project=args.project,
        limit=args.limit,
    )
    # Real token accounting for recalls (savings when an agent uses prior high-quality artifact).
    tokens_saved = getattr(args, "tokens_saved", None) or os.environ.get("RDN_TOKENS_SAVED")
    if tokens_saved:
        try:
            import rdn as reason
            reason.record_recall(args.query, tokens_saved=int(tokens_saved))
        except Exception:
            pass
    print(json.dumps({"results": results}, indent=2))


def cmd_resolve(args):
    node_url = _resolve_node_url(args)
    client = RDNClient(node_url=node_url)
    art = client.resolve(args.address)
    if art:
        print(json.dumps(art, indent=2))
    else:
        print(json.dumps({"status": "not_found", "address": args.address}, indent=2))
        sys.exit(1)

    # Real token accounting for resolves (savings from using the current canonical from Xport).
    tokens_saved = getattr(args, "tokens_saved", None) or os.environ.get("RDN_TOKENS_SAVED")
    if tokens_saved:
        try:
            import rdn as reason
            reason.record_recall(args.address, tokens_saved=int(tokens_saved))
        except Exception:
            pass


def cmd_status(args):
    node_url = _resolve_node_url(args)
    client = RDNClient(node_url=node_url)
    print("ReasonRDN status")
    print("  Node URL :", client.node_url or "local fallback only")
    print("  Broker   :", getattr(client, "broker_url", None) or "same as node")
    print("  Xport    :", getattr(client, "xport_url", None) or XPORT_URL, "(reason.astrognosy.com)")
    print("  Available:", client.available)
    print("  Local DB :", client.db_path)
    projects = client.get_recent_projects(8)
    print("  Recent projects:", ", ".join(projects) if projects else "(none yet)")
    hb = client.get_heartbeat()
    print("  7-day heartbeat:", hb)
    try:
        import rdn as reason
        recent = reason.get_recent_uris()
        print("  Recent URIs:", ", ".join(recent[:5]) if recent else "(none yet)")
        s = reason.status()
        top = s.get("top_prefixes", [])
        if top:
            print("  Top prefixes:", ", ".join(top))
    except Exception:
        pass


def cmd_xchange_arbitrate(args):
    node_url = _resolve_node_url(args)
    client = RDNClient(node_url=node_url)

    packages = []
    for p in args.package:
        if ":" not in p:
            print(f"Bad package format (need agent_id:answer): {p}")
            return
        aid, ans = p.split(":", 1)
        packages.append({"agent_id": aid.strip(), "answer_text": ans.strip()})

    result = client.xchange_arbitrate(
        query_text=args.query,
        packages=packages,
        reason_address=args.uri
    )
    print(json.dumps(result, indent=2))


def cmd_list(args):
    node_url = _resolve_node_url(args)
    client = RDNClient(node_url=node_url)
    results = client.list_prefix(args.prefix, limit=args.limit)
    print(json.dumps({"results": results}, indent=2))


def main():
    parser = argparse.ArgumentParser(
        prog="rdn",
        description="ReasonRDN memory substrate CLI. Easy for humans, perfect for agents. Supports auto-deposit to warf Xchange."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"rdn {__version__}",
    )
    parser.add_argument("--node", default=None, help="Override node URL (default: auto-discover local private node)")
    parser.add_argument(
        "--xchange", "--use-xchange", action="store_true",
        help="Use the warf Xchange broker (warf.astrognosy.com) for deposits/arbitration "
             "(scoring goes to astragnostic-api). Resolution uses Xport at reason.astrognosy.com. "
             "Equivalent to REASON_USE_XCHANGE=1. Great for ecosystem sharing."
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    p_rem = sub.add_parser("remember", help="Deposit a handoff / memory")
    p_rem.add_argument("content", help="The summary or content to remember")
    p_rem.add_argument("--project", default="astrognosy")
    p_rem.add_argument("--tags", default=None, help="Comma-separated tags")
    p_rem.add_argument("--tokens", default=None, help="Extra tokens for structural fingerprint (space separated)")
    p_rem.add_argument("--tokens-used", type=int, default=None, dest="tokens_used",
                       help="Tokens consumed to produce this handoff (for accurate harness metrics / token savings tracking)")
    p_rem.set_defaults(func=cmd_remember)

    p_rec = sub.add_parser("recall", help="Search memory")
    p_rec.add_argument("query", help="Search query")
    p_rec.add_argument("--project", default=None)
    p_rec.add_argument("--limit", type=int, default=10)
    p_rec.add_argument("--tokens-saved", type=int, default=None, dest="tokens_saved",
                       help="Tokens saved by using this recall (for accurate harness metrics)")
    p_rec.set_defaults(func=cmd_recall)

    p_res = sub.add_parser("resolve", help="Fetch exact artifact by reason:// address")
    p_res.add_argument("address")
    p_res.add_argument("--tokens-saved", type=int, default=None, dest="tokens_saved",
                       help="Tokens saved by resolving and using this artifact (for accurate harness metrics)")
    p_res.set_defaults(func=cmd_resolve)

    p_stat = sub.add_parser("status", help="Show current node/client status + heartbeat")
    p_stat.set_defaults(func=cmd_status)

    # Xchange-specific convenience subcommands (full broker flow)
    p_xarb = sub.add_parser("xchange-arbitrate", help="Submit packages for full Xchange arbitration (hits broker -> astragnostic-api)")
    p_xarb.add_argument("query", help="The query / problem being arbitrated")
    p_xarb.add_argument("--package", action="append", required=True,
                        help="agent_id:answer_text (repeatable). Example: --package agent1:the answer")
    p_xarb.add_argument("--uri", help="Optional reason:// URI for promotion target")
    p_xarb.set_defaults(func=cmd_xchange_arbitrate)

    # List / browse prefix (new for namespace exploration)
    p_list = sub.add_parser("list", help="List artifacts under a reason:// prefix (browse the namespace with partial URIs)")
    p_list.add_argument("prefix", help="e.g. reason://grok or grok/build or warf")
    p_list.add_argument("--limit", type=int, default=20, help="Max results to show")
    p_list.set_defaults(func=cmd_list)

    # The magical one-liner experience
    p_start = sub.add_parser("start", help="The easiest way to start using rdn. Launches the badass agnostic harness dashboard with full excitement and metrics.")
    p_start.set_defaults(func=lambda args: launch_harness())

    args = parser.parse_args()
    if hasattr(args, "cmd") and args.cmd == "start":
        launch_harness()
    else:
        args.func(args)


def launch_harness():
    """The magical one-liner 'start using rdn' experience."""
    print("\n" + "="*70)
    print("🚀 START USING RDN — THE AGNOSTIC HARNESS IS NOW LIVE")
    print("="*70)
    print("""
Instant features you just gained (first-run tour — what you unlocked):
• Persistent local mirror (private node at 8765 + SQLite) that works offline and survives agent sessions
• Real token accounting: report --tokens-used when depositing; get accurate savings when you (or agents) resolve prior external winners
• Easy bridge to the external WARF network flywheel: set REASON_USE_XCHANGE=1 or use --xchange; supply a reason:// URI and a strong artifact can compete under Xtend (in astragnostic-api) to become the new canonical for that URI on the public Xport (reason.astrognosy.com)
• IP-safe by design: local structural fingerprints are the hardcoded protected output from _pcf.py; the real PCF + Xtend scoring and promotion live in the external engine
• Live harness metrics (token savings from external promoted artifacts, velocity, ship rate, vibe stars) + flywheel-aware suggestions that nudge you to produce high-signal deposits worth promoting
• Unified `import rdn as reason` + CLI/MCP/dash that all feed the same coherent surface

This is the production-grade on-ramp to the full Astrognosy WARF / reason:// stack. Local-first, ecosystem-native, ridiculously useful.

Launching the full visual harness now...
""")
    try:
        import subprocess, sys
        # Proper launch for the Streamlit dashboard (the visual harness)
        subprocess.run([sys.executable, "-m", "streamlit", "run", "rdn/dash.py"], check=False)
    except Exception:
        print("\nTo launch the badass dashboard:")
        print("  pip install 'reason-rdn[dash]'")
        print("  rdn start")
        print("  # or: python -m rdn.dash")


if __name__ == "__main__":
    main()
