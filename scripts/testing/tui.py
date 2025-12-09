#!/usr/bin/env python3
"""Launcher for the VaultMind Forge TUI"""
from vaultmind_forge.cli.tui_app import VaultMindApp

if __name__ == "__main__":
    app = VaultMindApp()
    app.run()
