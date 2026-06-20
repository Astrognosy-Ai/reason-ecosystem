#!/usr/bin/env python
"""
install.py - Reason Ecosystem Unified Installer (coherent v2)

One-command installer for the ReasonRDN shared memory substrate:

- rdn core package (unified client, structural fingerprint handoffs,
  embedded private node, first-class MCP tools)
- Optional desktop GUI (ReasonRDN console)
- Private node auto-start for local use
- Git hook + repo-state sync automation
- Automatic MCP registration for agents (Claude, Grok, Cursor, etc.)

The Positional Correlation Fields (PCF) algorithm is used to generate
stable, high-quality handoff fingerprints.

Usage (from the ReasonRDN root):
  py -3.13 install.py
  py -3.13 install.py --no-service          # skip windows integration
  py -3.13 install.py --agent-only          # just the memory + MCP bits
  py -3.13 install.py --build               # also build the ReasonRDN.exe

After install you get working:
  import rdn
  from rdn.handoff import ReasonRDN
  rdn-sync --once
  rdn-mcp
  rdn-node
  (and the GUI via gui/app.py or the built exe)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

CREATE_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)

ECOSYSTEM_ROOT = Path(__file__).resolve().parent
HOME = Path.home()
CONFIG_FILE = HOME / ".reason-ecosystem.cfg"
DEFAULT_PORT = 8765


def run(cmd, cwd=None, quiet=False, check=True, env=None):
    print("+", " ".join(map(str, cmd)))
    try:
        res = subprocess.run(cmd, cwd=cwd, capture_output=quiet, text=True, env=env)
        if not quiet:
            if res.stdout:
                print(res.stdout, end="")
            if res.stderr:
                print(res.stderr, file=sys.stderr)
        if check and res.returncode != 0:
            raise subprocess.CalledProcessError(res.returncode, cmd, output=res.stdout, stderr=res.stderr)
        return res
    except Exception:
        raise


def install_core():
    """Install the rdn package (and optional GUI/MCP extras)."""
    print("\n=== Installing coherent reason-rdn package ===")
    # Always from the ecosystem root so packages=rdn is found cleanly
    print("Installing editable core (rdn + console scripts)...")
    run([sys.executable, "-m", "pip", "install", "-e", ".", "--upgrade"], cwd=ECOSYSTEM_ROOT)

    print("Installing optional GUI runtime (customtkinter)...")
    try:
        run([sys.executable, "-m", "pip", "install", "customtkinter", "--upgrade"], cwd=ECOSYSTEM_ROOT, quiet=True)
    except Exception:
        print("  (customtkinter install had issues - GUI may need manual `pip install customtkinter`)")

    return True


def start_private_node(port: int, storage: str) -> tuple[int | None, int]:
    """Start the embedded node using the new coherent -m entrypoint.
    Returns (PID, actual_port). The node may bind a different port if the
    requested one is in use; we always return the one it actually used.
    """
    storage_path = Path(storage)
    storage_path.mkdir(parents=True, exist_ok=True)
    print(f"\nStarting embedded private ReasonRDN node on port {port}, storage={storage_path}")

    cmd = [
        sys.executable, "-m", "rdn.node.server",
        "--host", "127.0.0.1",
        "--port", str(port),
        "--storage", str(storage_path),
    ]
    proc = subprocess.Popen(cmd, creationflags=CREATE_NO_WINDOW)

    # Wait for the port file (written by the node after successful bind)
    port_file = storage_path / "private-node.port"
    for _ in range(50):
        if port_file.exists():
            try:
                p_text = port_file.read_text(encoding="utf-8").strip()
                if p_text:
                    actual = int(p_text)
                    print(f"Private node started on port {actual} (PID: {proc.pid})")
                    return proc.pid, actual
            except Exception:
                pass
        time.sleep(0.2)

    print("Warning: node did not write port file in time; using requested port as fallback.")
    return proc.pid, port


def create_unified_config(port: int, node_url: str | None = None):
    """Create ~/.reason-ecosystem.cfg pointing at the private (or supplied) node."""
    print("\n=== Writing unified config ===")
    if node_url is None:
        node_url = f"http://127.0.0.1:{port}"

    config = {
        "version": "2.0",
        "node_url": node_url,
        "port": port,
        "private_storage": str(HOME / ".reason-rdn" / "private-node"),
        "memory_db": str(HOME / ".reason-rdn" / "private-node" / "warf-node.db"),
        "mcp_enabled": True,
        "installed_at": str(int(time.time())),
    }

    CONFIG_FILE.write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(f"Config written to: {CONFIG_FILE}")
    print(f"  node_url: {node_url}")
    return config


def register_mcp():
    """
    Aggressively register the MCP server so that agents and coding assistants
    (Claude, Grok, Cursor, Windsurf, Cline, Continue.dev, etc.) can use it
    with almost zero configuration after the one-liner install.

    This is a key part of being "immediately configured by any agent".
    """
    print("\n=== Registering ReasonRDN MCP server for agents ===")

    # 1. Generic copilot / older style
    try:
        copilot_config = HOME / ".copilot" / "mcp.yml"
        copilot_config.parent.mkdir(parents=True, exist_ok=True)
        content = copilot_config.read_text(encoding="utf-8") if copilot_config.exists() else ""
        if "ReasonRDN" not in content and "rdn-mcp" not in content:
            entry = f"""
# ReasonRDN - shared memory substrate for agents (protected structural fingerprints)
ReasonRDN:
  command: python
  args: ["-m", "rdn.mcp.server"]
  env:
    REASON_ECOSYSTEM_CONFIG: "{CONFIG_FILE}"
"""
            with open(copilot_config, "a", encoding="utf-8") as f:
                f.write(entry)
            print(f"  + {copilot_config}")
    except Exception as e:
        print(f"  (non-fatal) copilot mcp.yml: {e}")

    # 2. Claude Desktop (very common)
    try:
        # Windows typical path
        claude_config = HOME / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json"
        if not claude_config.exists():
            # macOS / Linux common alternatives
            claude_config = HOME / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
        if not claude_config.exists():
            claude_config = HOME / ".config" / "Claude" / "claude_desktop_config.json"

        claude_config.parent.mkdir(parents=True, exist_ok=True)

        existing = {}
        if claude_config.exists():
            try:
                existing = json.loads(claude_config.read_text(encoding="utf-8"))
            except Exception:
                existing = {}

        mcp_servers = existing.setdefault("mcpServers", {})
        if "reasonrdn" not in mcp_servers:
            mcp_servers["reasonrdn"] = {
                "command": "python",
                "args": ["-m", "rdn.mcp.server"],
                "env": {
                    "REASON_ECOSYSTEM_CONFIG": str(CONFIG_FILE)
                }
            }
            claude_config.write_text(json.dumps(existing, indent=2), encoding="utf-8")
            print(f"  + Claude Desktop: {claude_config}")
        else:
            print("  Claude Desktop already has a reasonrdn entry")
    except Exception as e:
        print(f"  (non-fatal) Claude Desktop registration: {e}")

    # 3. Generic .mcp.json in home (many tools look for this pattern)
    try:
        generic = HOME / ".mcp.json"
        data = {}
        if generic.exists():
            try:
                data = json.loads(generic.read_text(encoding="utf-8"))
            except Exception:
                data = {}
        servers = data.setdefault("servers", {})
        if "reasonrdn" not in servers:
            servers["reasonrdn"] = {
                "command": "python",
                "args": ["-m", "rdn.mcp.server"]
            }
            generic.write_text(json.dumps(data, indent=2), encoding="utf-8")
            print(f"  + Generic MCP config: {generic}")
    except Exception as e:
        print(f"  (non-fatal) .mcp.json: {e}")

    print("  Direct usage:  rdn-mcp    or    python -m rdn.mcp.server")
    print("  The memory layer should now be visible to most agents automatically.")

    # Print PATH hint so rdn / rdn-start etc. work in the current shell
    scripts_dir = str(HOME / "AppData" / "Local" / "Programs" / "Python" / "Python313" / "Scripts")
    print(f"\nNOTE: If 'rdn' command is not found in this PowerShell session, run:")
    print(f'  $env:Path = "{scripts_dir};" + $env:Path')
    print("  (For permanent fix, add that Scripts folder to your user PATH in System Properties > Environment Variables.)")

def main(argv=None):
    parser = argparse.ArgumentParser(description="Reason Ecosystem installer (coherent unified memory)")
    parser.add_argument("--operator-only", action="store_true", help="Install core + GUI bits (default behavior)")
    parser.add_argument("--agent-only", action="store_true", help="Install core + MCP/agent tools only (skip GUI auto-start)")
    parser.add_argument("--build", action="store_true", help="After install, build ReasonRDN.exe via PyInstaller (slow)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="Private node port (default 8765)")
    parser.add_argument("--no-service", action="store_true", help="Skip Windows Task Scheduler / shim integration")
    parser.add_argument("--node-url", default=None, help="Use a remote/shared node instead of starting a private one")
    parser.add_argument(
        "--xchange", "--use-xchange", action="store_true",
        help="Configure auto-deposit to the warf Xchange reference broker (https://warf.astrognosy.com on Railway). "
             "Deposits flow through the broker to astragnostic-api (AWS ECS) for real PCF scoring + possible "
             "promotion to the reason:// registry. This is the production collective intelligence path."
    )
    args = parser.parse_args(argv)

    try:
        install_core()

        node_pid = None
        effective_node_url = args.node_url
        effective_port = args.port

        if args.xchange:
            effective_node_url = "https://warf.astrognosy.com"
            print("\n*** Configuring for warf Xchange (https://warf.astrognosy.com) ***")
            print("    Reasoning artifacts will auto-deposit to the central exchange (with local mirror if enabled).")
            print("    For authenticated access set REASON_RDN_TOKEN (or RDN_AUTH_TOKEN) in your environment.")
            print("    Local private node startup is skipped when using --xchange (you can still run one manually).")

        if not args.agent_only:
            # Start a private node for local-first (unless remote/Xchange provided)
            if effective_node_url:
                print(f"\nUsing remote node: {effective_node_url}")
            else:
                node_pid, actual_port = start_private_node(args.port, str(HOME / ".reason-rdn" / "private-node"))
                # Use the port the node actually bound to (it may differ if 8765 was busy)
                effective_port = actual_port
            time.sleep(0.8)

        # Always create the unified config (with Xchange or provided URL)
        config = create_unified_config(effective_port, effective_node_url)

        # Register MCP for agents
        register_mcp()

        print("\n=== Installation Complete ===")
        print(f"Config: {CONFIG_FILE}")
        print(f"Node URL: {config['node_url']}")
        print(f"Local DB:   {config['memory_db']}")
        if "warf.astrognosy.com" in str(config.get("node_url", "")):
            print("    (warf Xchange broker configured - deposits will be scored by astragnostic-api on AWS)")

        print("\n" + "="*70)
        print("🚀 THE EASY 'START USING RDN' (HERO PATH - RELIABLE, CROSS-PLATFORM)")
        print("="*70)

        # Context-aware hero path
        is_local_source = (ECOSYSTEM_ROOT / "pyproject.toml").exists()
        if is_local_source:
            print("""
You're running from the local source tree.

To get the full experience (dashboard + real token metrics + extras) right now:
  py -3.13 -m pip install -e '.[full]'
  rdn start

(The published one-liner below will work once reason-rdn is on PyPI.)
""")
        else:
            print("""
The primary, reliable way (no bundling issues):
  pip install 'reason-rdn[full]' && rdn start
""")

        print("""
This launches the full exciting harness dashboard with:
- Live metrics (real token savings from external promoted artifacts, velocity, ship rate, vibe stars)
- Workflow suggestions (Xtend/promotion aware)
- Xchange controls and reason:// explorer
- The coherent on-ramp experience that feeds the external WARF flywheel

Tell agents: "install reason-rdn[full] and run rdn start"   (or the local -e version above)

See the full one-liner, ports (8765=node, 8501=dash), and EXE notes in README.md.
""")

        if not args.agent_only:
            print("\nOperator / GUI (for the EXE, see README for the simplified one-stop rdn.exe):")
            print("  Run from source:  python gui/app.py")
            print("  Or the built exe: dist\\rdn.exe (or the portable zip)")
            if node_pid:
                print(f"  Private node PID: {node_pid}")

        print("\nAgent / MCP tools:")
        print("  python -m rdn.mcp.server")
        print("  (or the rdn-mcp console script after PATH refresh)")

        print("\nCLI (the coherent API):")
        print("  rdn remember \"Fixed the race condition in sync\" --tags infra,bugfix")
        print("  rdn recall \"race condition\"")
        print("  rdn status")
        print("  rdn --xchange recall \"handoff\"     # explicitly target the Xchange")
        print("  rdn-sync --once --install-hooks")
        print("  rdn-node")
        print("  rdn-mcp")

        if "warf.astrognosy.com" in str(config.get("node_url", "")):
            print("\n  To also use the Xchange from agents: set REASON_USE_XCHANGE=1 or pass --xchange to tools.")

        # Optional build - the modern one-stop .exe (CLI + badass harness dashboard)
        if args.build:
            print("\n=== Building the one-stop rdn.exe (full coherent harness) ===")
            try:
                run([sys.executable, "-m", "pip", "install", "pyinstaller", "--upgrade"],
                    cwd=ECOSYSTEM_ROOT, quiet=True)
                # Use the new root package.py which builds rdn_launcher.py
                # This produces dist/rdn.exe - the true one-stop experience
                run([sys.executable, "package.py"], cwd=ECOSYSTEM_ROOT)
                print("\nOne-stop build complete!")
                print("  dist/rdn.exe          - double-click for dashboard + metrics + system tray (auto node + MCP controls)")
                print("  dist/rdn-portable.zip - convenient distribution package")
                print("  From cmd: rdn.exe remember \"...\"   or   rdn.exe start")
            except Exception as e:
                print(f"Build step failed (non-fatal for core): {e}")
                print("You can also run manually: python package.py")

        # Windows integration (best effort, non-fatal)
        if not args.no_service and not args.agent_only:
            print("\n=== Windows integration (optional) ===")
            try:
                # The legacy helper lived under operator/scripts/. It may or may not exist in legacy-operator/.
                # We keep this best-effort so old installs don't explode.
                legacy_script = ECOSYSTEM_ROOT / "legacy-operator" / "scripts" / "register_windows_integration.py"
                if legacy_script.exists():
                    run([sys.executable, str(legacy_script)], cwd=ECOSYSTEM_ROOT)
                else:
                    print("  (skipped) No legacy windows integration helper found. "
                          "You can run the GUI manually or create a startup shortcut to gui/app.py or the .exe.")
            except Exception as e:
                print(f"  Windows integration helper: {e} (non-fatal)")

        print("\n" + "="*70)
        print("🚀 START USING RDN - ONE LINER EDITION")
        print("="*70)
        print("""
The easiest way:
  pip install 'reason-rdn[full]'
  rdn start

Instantly gained:
• Model-agnostic persistent memory (local + full warf Xchange)
• Auto-deposit → broker (warf.astrognosy.com) → astragnostic-api scoring → reason:// Xport
• Protected fingerprints + live harness metrics (tokens saved, velocity, ship rate, vibe stars)
• Workflow suggestions that improve how you actually ship
• Beautiful dashboard that shows the entire stack in one place

This is the coherent agnostic harness. One memory layer. Every agent. Forever.
""")

        return args

    except Exception as exc:
        print(f"\nInstallation failed: {exc}")
        sys.exit(2)


if __name__ == "__main__":
    main()
