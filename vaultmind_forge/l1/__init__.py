"""LPG-L1 support utilities.

Small, dependency-light helpers that support the LPG-L1 lifecycle system but are
not themselves part of the authority layer. Nothing in here grants capability,
records approval, or makes a decision that the scanner and its schemas own.

Contents:
- `web_reader`: fetch a URL and reduce it to main content as text, so agents
  gathering reference material are not swamped by site chrome. Standard library
  only, read-only, no credentials.
"""

from __future__ import annotations

__all__ = ["web_reader"]
