#!/usr/bin/env python3
"""
Tiny bootstrap for reason-rdn — the coherent agnostic harness.

Run this one-liner (no prior install needed):

    python -c "$(curl -fsSL https://raw.githubusercontent.com/Astrognosy/reason-ecosystem/main/bootstrap.py)"

Or save it and run:
    python bootstrap.py

This will:
1. Ensure the package is installed with the full experience (dash + mcp + cli)
2. Print the magical "start using rdn" one-liner
3. Optionally launch the harness dashboard immediately

It solves the "I want persistent memory + metrics + Xchange flywheel RIGHT NOW" problem for any agent or human.

After this, agents get:
- One import: import rdn as reason
- Auto Xchange federation (when you want it)
- Real token savings tracking, velocity, ship rate, vibe stars, workflow suggestions
- The beautiful dashboard that makes the value obvious instantly

This is the on-ramp to the warf reasoning substrate. High-quality handoffs you create here can eventually become callable deterministic artifacts in the network.

(Shhh — the long game is turning inference into resolution.)
"""

import os
import subprocess
import sys
import tempfile
import urllib.request

def main():
    print("\n" + "=" * 72)
    print("🚀 BOOTSTRAPPING THE REASON AGNOSTIC HARNESS")
    print("=" * 72)
    print("""
This tiny script gets you the full coherent experience:
• Persistent cross-agent memory (local + warf Xchange)
• Protected structural fingerprints + real metrics
• Token savings, velocity, ship rate, vibe stars tracked automatically
• Workflow suggestions that improve how you ship
• One beautiful dashboard that shows the entire stack

The one-liner you (and your agents) will love:
    pip install 'reason-rdn[full]' && rdn start
""")

    # Minimal dependency bootstrap — install the full experience
    print("Installing reason-rdn[full] (this gives you the dash, MCP, and coherent API)...")
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--upgrade",
            "reason-rdn[full]"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("✓ Installed.")
    except Exception as e:
        print(f"Install step had an issue (you may need to run pip manually): {e}")
        print("You can still do: pip install 'reason-rdn[full]'")

    print("\n" + "-" * 72)
    print("✅ You're ready.")
    print("\nThe magic one-liner (the easy 'start using rdn'):")
    print("    pip install 'reason-rdn[full]' && rdn start")
    print("\nThis launches the full exciting harness dashboard with metrics (token savings, velocity, ship rate, vibe stars), suggestions, and Xchange controls.")
    print("\nOr just run now:")
    print("    rdn start")
    print("\nIn code (the simplest coherent API agents love):")
    print("    import rdn as reason")
    print("    reason.remember(\"Fixed the critical thing...\", tags=[\"infra\"])")
    print("    print(reason.harness_metrics())   # real token savings + suggestions")
    print("\nWhen you're ready to feed the flywheel (auto-deposit to Xchange):")
    print("    REASON_USE_XCHANGE=1 rdn start")
    print("\n(Shhh — every high-quality artifact you create here helps turn")
    print(" inference into resolution across the network. The meganode grows with every share.)")
    print("=" * 72 + "\n")

    # Optional auto-launch the dashboard for instant wow
    if "--no-launch" not in sys.argv:
        try:
            print("Launching the harness dashboard so you see the value immediately...")
            subprocess.run([sys.executable, "-m", "rdn.dash"], check=False)
        except Exception:
            print("Run `rdn start` manually to see the full visual experience.")

if __name__ == "__main__":
    main()
