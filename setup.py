"""
Legacy shim.

This project is now built with pyproject.toml (PEP 621).
Use:

    pip install -e ".[full]"
    pip install -e ".[mcp]"

or simply:

    pip install -e .

All console scripts (rdn, rdn-mcp, rdn-node, rdn-sync) are declared in pyproject.toml.
"""

from setuptools import setup

# All real metadata lives in pyproject.toml
setup()
