"""
rdn.dash — Badass web dashboard for the coherent ReasonRDN / WARF / Xchange stack.

Launch with:
  rdn-dash
  or
  python -m rdn.dash
  or
  streamlit run -m rdn.dash   (after `pip install 'reason-rdn[dash]'`)

This file is structured to avoid the "Runtime instance already exists!" error.

- ALL Streamlit UI code lives inside _app().
- launch() is a *thin* launcher used ONLY by the console script / direct execution.
- When Streamlit itself runs the module, it safely executes _app().
- No st.* calls outside _app().
- No self-launching stcli logic inside the app execution path.
"""

from __future__ import annotations

import os
import json
import hashlib
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    import streamlit as st
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError:
    print("Install with: pip install 'reason-rdn[dash]' or 'reason-rdn[full]'")
    raise

import rdn as reason  # THE coherent API
from rdn.client import XCHANGE_BROKER_URL, XPORT_URL  # for display only
from rdn.handoff import sync as rdn_sync


# ============================================================
#  UI HELPERS (safe to call from _app only)
# ============================================================

def render_fingerprint_viz(structural_hash: str, label: str = "STRUCTURAL FINGERPRINT") -> None:
    """Badass but safe visualization of the protected structural_hash."""
    if not structural_hash:
        st.write("No fingerprint")
        return

    cols = st.columns(8)
    for i, char in enumerate(structural_hash[:32]):
        intensity = int(char, 16) / 15.0
        hue = (i * 17) % 360
        color = f"hsl({hue}, 70%, {30 + intensity * 40}%)"
        with cols[i % 8]:
            st.markdown(
                f'<div style="background:{color}; width:28px; height:28px; border-radius:4px; margin:2px;"></div>',
                unsafe_allow_html=True,
            )
    st.caption(f"{label} • {structural_hash[:16]}... (protected PCF output)")


# ============================================================
#  THE ACTUAL DASHBOARD — ALL STREAMLIT CODE LIVES INSIDE _app()
# ============================================================

def _app():
    """The actual Streamlit application. 
    Streamlit executes THIS when it runs the script.
    """

    # --- Page config ---
    st.set_page_config(
        page_title="Reason • WARF Xchange",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # --- Theme ---
    st.markdown(
        """
        <style>
        .stApp { background: #0a0a0f; color: #e0e0ff; }
        .stButton>button { background: #7c6af5; color: white; border: none; border-radius: 8px; }
        .stButton>button:hover { background: #5a4ed1; }
        .metric-card { background: #13131a; border: 1px solid #2a2a3a; border-radius: 12px; padding: 16px; }
        .reason-uri { font-family: 'SF Mono', monospace; color: #7c6af5; }
        .fingerprint-viz { font-family: monospace; letter-spacing: 2px; }
        h1, h2, h3 { color: #c0c0ff; }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- Header ---
    st.title("🧠 reason — The Agnostic Harness")
    st.markdown("""
    **One command. Instant superpowers.**

    Persistent memory across every agent and session.  
    Auto-share to the WARF Xchange (warf.astrognosy.com → astragnostic-api at api.pcfic.com for Xtend scoring vs current placeholder + corpus).  
    Protected local structural fingerprints (real PCF/Xtend lives externally; local only safe outputs).  
    Xport at reason.astrognosy.com + xport.astrognosy.com for public canonical resolution.

    Live metrics: real token savings (from external promoted winners), velocity, ship rate, vibe stars + suggestions.

    This is your model-agnostic on-ramp to the full WARF + Pacific engine (grand master at api.pcfic.com). Local-first + bridge to the external flywheel.
    """)

    # Big excitement / default response — first-run "what you unlocked" tour
    st.success("🚀 You just leveled up. Your agents now have perfect recall across sessions, the ability to feed high-quality artifacts into the external WARF network (where Xtend can promote winners to become the new canonical for a reason:// URI), and this dashboard shows exactly how many tokens you're saving by resolving prior promoted artifacts instead of re-reasoning — plus suggestions to produce winners yourself. Report `tokens_used` on deposits for the most accurate numbers. This is production agent memory.")

    # --- Sidebar toggle ---
    # Xchange sharing is now the default (you can still opt out for purely local use)
    use_xchange = st.sidebar.checkbox(
        "XCHANGE MODE — feed the collective (broker → astragnostic → Xport)  [default: ON]",
        value=True,
        help="When enabled (the default), deposits go through the full external WARF network for scoring and potential Xtend promotion to a canonical reason:// URI."
    )

    # --- Status ---
    st.subheader("Harness Status & Impact")
    status = reason.status()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Local Node", "🟢 Online" if status.get("local_available") else "🔴 Offline", "private + Xchange mirror")
    with col2:
        st.metric("Xchange Broker", "🟢 warf.astrognosy.com", "Railway → astragnostic")
    with col3:
        st.metric("Xport Registry", "🟢 reason.astrognosy.com + xport.astrognosy.com", "Public canonicals")
    with col4:
        st.metric("Mode", "FULL HARNESS" if use_xchange else "LOCAL + BRIDGE", "IP-safe fingerprints locally")

    # --- Metrics ---
    st.subheader("Your Impact (Agnostic Harness Metrics)")
    m = reason.harness_metrics() if hasattr(reason, "harness_metrics") else status

    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    with mcol1:
        st.metric("💰 Tokens Saved (est.)", f"{m.get('estimated_tokens_saved', 0):,}", "vs re-reasoning from scratch")
    with mcol2:
        st.metric("⚡ Velocity", f"{m.get('velocity', 0)}", "handoffs per active cycle")
    with mcol3:
        st.metric("🚢 Ship Rate", f"{m.get('ship_rate', 0)}%", "handoffs that became useful recalls")
    with mcol4:
        st.metric("⭐ Vibe Stars", m.get('vibe_stars', 0), "positive signals & shares")

    if m.get("suggestions"):
        st.info("**Workflow Suggestions** (harness intelligence)")
        for s in m["suggestions"]:
            st.write(f"• {s}")

    st.divider()

    # ============================================================
    #  DEPOSIT FORM
    # ============================================================

    with st.container(border=True):
        st.markdown("### Deposit — Instant Value")
        st.caption("Every deposit gives you memory that survives, feeds the network, and gets tracked in your harness metrics.")

        col_a, col_b = st.columns([3, 1])
        with col_a:
            content = st.text_area("Content / Insight / Handoff", height=100, placeholder="Fixed the critical race in the handoff protocol using structural correlation...")
            project = st.text_input("Project / Domain", value="astrognosy")
            tags = st.text_input("Tags (comma separated)", value="handoff,infra")
            col_prefix, col_rest = st.columns([1.1, 4])
            with col_prefix:
                st.markdown("**reason://**")
            with col_rest:
                uri_rest = st.text_input("URI suffix for Xport promotion (optional)", 
                                         value="", label_visibility="collapsed",
                                         placeholder="grok/build/test   or   warf/decision-theory/...")
            uri = f"reason://{uri_rest}" if uri_rest else None
            tokens_used = st.number_input("Tokens used to produce this (optional, for accurate harness metrics)", min_value=0, value=0, step=100, help="Report the real token cost of the work that produced this artifact. Used for precise savings tracking when others resolve it later.")
        with col_b:
            target_xchange = st.checkbox("Send to Xchange (broker → astragnostic)", value=use_xchange)
            st.caption("This is how you 'start using rdn' at scale. Local mirror always happens.")

            if st.button("🚀 DEPOSIT TO HARNESS", use_container_width=True, type="primary"):
                tags_list = [t.strip() for t in tags.split(",") if t.strip()]
                meta = {"reason_uri": uri} if uri else {}
                tu = int(tokens_used) if tokens_used and tokens_used > 0 else None
                res = reason.remember(content, uri=uri, tags=tags_list, project=project, meta=meta, tokens_used=tu)
                st.success(f"Deposited. Your harness metrics just updated (tokens_used recorded if provided). structural_hash: {res.get('structural_hash', 'N/A')[:16]}...")

                if res.get("structural_hash"):
                    st.markdown("**Protected Structural Fingerprint (PCF output — safe & powerful)**")
                    render_fingerprint_viz(res["structural_hash"])

    # ============================================================
    #  REASON:// EXPLORER (Xport resolution)
    # ============================================================

    with st.container(border=True):
        st.markdown("### reason:// Explorer (Xport)")

        # Session state for prefix input persistence
        if "explorer_prefix" not in st.session_state:
            st.session_state.explorer_prefix = ""

        # Use module-level recent URIs for cross-session persistence
        try:
            import rdn as reason
            recent_uris = reason.get_recent_uris()
        except Exception:
            recent_uris = []

        col_prefix2, col_rest2 = st.columns([1.1, 4])
        with col_prefix2:
            st.markdown("**reason://**")
        with col_rest2:
            uri_rest2 = st.text_input(
                "Partial or full URI (supports prefix browsing)",
                value=st.session_state.explorer_prefix,
                key="explorer_input",
                label_visibility="collapsed",
                placeholder="warf   or   warf/build   or   grok/build/test"
            )
            if uri_rest2 != st.session_state.explorer_prefix:
                st.session_state.explorer_prefix = uri_rest2

        uri = f"reason://{uri_rest2}" if uri_rest2 else None

        if st.button("🔍 RESOLVE / BROWSE PREFIX", use_container_width=True):
            if uri:
                # Try exact first
                art = reason.resolve(uri)
                if art:
                    st.json(art)
                    if art.get("structural_hash"):
                        render_fingerprint_viz(art["structural_hash"], "RESOLVED FINGERPRINT")
                else:
                    # Prefix / incomplete URI browse with recursive tree view
                    matches = reason.list_prefix(uri, limit=30)
                    if matches:
                        st.success(f"**{len(matches)}** artifact(s) under or matching **{uri}**")

                        # Build nested tree structure
                        def build_tree(items, base):
                            tree = {}
                            for m in items:
                                addr = m.get("address", "")
                                if not addr.startswith(base):
                                    continue
                                rel = addr[len(base):].lstrip("/")
                                parts = [p for p in rel.split("/") if p]
                                current = tree
                                for i, part in enumerate(parts):
                                    if i == len(parts) - 1:
                                        current.setdefault(part, []).append(m)
                                    else:
                                        current = current.setdefault(part, {})
                            return tree

                        def render_tree(node, current_path=""):
                            for key in sorted(node.keys()):
                                full_path = f"{current_path}/{key}".lstrip("/")
                                full_uri = f"{uri.rstrip('/')}/{full_path}".rstrip("/")
                                if isinstance(node[key], dict):
                                    with st.expander(f"📁 {key}"):
                                        render_tree(node[key], f"{current_path}/{key}".lstrip("/"))
                                else:
                                    items = node[key]
                                    with st.expander(f"📄 {key} ({len(items)})", expanded=True):
                                        for m in items:
                                            addr = m.get("address", full_uri)
                                            col1, col2 = st.columns([6, 1])
                                            with col1:
                                                st.markdown(f"**{addr}**")
                                                st.code(addr, language=None)  # easy to copy
                                                content = m.get("content", "")
                                                st.write(content[:350] + ("..." if len(content) > 350 else ""))
                                                if m.get("structural_hash"):
                                                    render_fingerprint_viz(m["structural_hash"])
                                                st.caption(f"Project: {m.get('project', '?')} • {m.get('deposited_at', '')[:16]}")
                                            with col2:
                                                if st.button("📋", key=f"use_{addr}", help="Load this URI"):
                                                    st.session_state.explorer_prefix = addr.replace("reason://", "")
                                                    try:
                                                        import rdn as reason
                                                        reason.add_recent_uri(addr)
                                                    except Exception:
                                                        pass
                                                    st.toast(f"Loaded {addr}")
                                                    st.rerun()

                        tree = build_tree(matches, uri)
                        render_tree(tree)
                    else:
                        st.warning(f"No exact match and no artifacts found under the prefix **{uri}**.")

        # Recent URIs (persisted via reason module for cross-session)
        try:
            import rdn as reason
            recent_uris = reason.get_recent_uris()
        except Exception:
            recent_uris = []
        if recent_uris:
            st.caption("Recent URIs (click to load)")
            rec_cols = st.columns(min(4, len(recent_uris)))
            for i, rec in enumerate(recent_uris[:4]):
                with rec_cols[i]:
                    if st.button(rec.replace("reason://", ""), key=f"recent_{i}"):
                        st.session_state.explorer_prefix = rec.replace("reason://", "")
                        try:
                            import rdn as reason
                            reason.add_recent_uri(rec)
                        except Exception:
                            pass
                        st.rerun()

    # ============================================================
    #  ACTIVITY
    # ============================================================

    st.subheader("Activity & Visuals")
    tab1, tab2 = st.tabs(["Recent Handoffs", "Fingerprint Gallery"])

    with tab1:
        # Simple recall (coherent API)
        from rdn.client import RDNClient
        c = RDNClient()
        if use_xchange:
            c.broker_url = XCHANGE_BROKER_URL
            c.xport_url = XPORT_URL
        recent = c.recall("handoff", limit=8)
        if recent:
            for item in recent:
                with st.expander(f"{item.get('project', 'unknown')} • {item.get('deposited_at', '')[:16]}"):
                    st.write(item.get("content", ""))
                    if item.get("structural_hash"):
                        render_fingerprint_viz(item["structural_hash"])
        else:
            st.info("No recent handoffs yet. Deposit something above.")

    with tab2:
        st.caption("Safe visualizations of structural fingerprints (never the PCF math itself)")
        # Demo gallery
        demo_hashes = [
            hashlib.sha256(b"demo1").hexdigest(),
            hashlib.sha256(b"demo2").hexdigest(),
            hashlib.sha256(b"demo3").hexdigest(),
        ]
        cols = st.columns(3)
        for i, h in enumerate(demo_hashes):
            with cols[i]:
                st.markdown(f"**Demo {i+1}**")
                render_fingerprint_viz(h)

    # Footer coherence note
    st.caption(
        "Local harness (this) + warf.astrognosy.com (broker) + api.pcfic.com (astragnostic grand master for WARF + Pacific) + reason.astrognosy.com / xport.astrognosy.com (Xport registry). "
        "Local fingerprints are safe outputs only; real Xtend scoring + promotion lives externally."
    )

    if st.button("🔄 Refresh Stack"):
        st.rerun()


# ============================================================
#  THIN LAUNCHER — ONLY FOR CONSOLE SCRIPT / DIRECT EXECUTION
# ============================================================

def launch():
    """Console script entry point for `rdn-dash`.

    This is a *thin* launcher. It must never contain any Streamlit UI
    commands itself (no st.set_page_config, st.title, etc.).

    When you run `rdn-dash`, this tells Streamlit to run this file.
    Streamlit then re-imports the module in a properly initialized runtime
    and executes the real app code inside _app().
    """
    import sys
    from streamlit.web import cli as stcli

    if len(sys.argv) > 1 and sys.argv[1] in ("--help", "-h"):
        print("Badass Reason + WARF Xchange Dashboard")
        print("Run: rdn-dash")
        print("      streamlit run -m rdn.dash")
        return

    sys.argv = ["streamlit", "run", __file__]
    sys.exit(stcli.main())


if __name__ == "__main__":
    # When running directly with `python -m rdn.dash` or
    # `streamlit run rdn/dash.py`, call the actual app.
    # The console script (rdn-dash) calls launch() directly via the entry point.
    _app()