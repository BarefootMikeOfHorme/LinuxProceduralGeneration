"""
Run from repo root to create the minimal module files for VaultMind Forge.
"""
from pathlib import Path
import sys
import textwrap

root = Path(".").resolve()
to_create = {
 "vaultmind_forge/__init__.py": '''# auto-generated init
__all__ = ["forge_cli","forge_agent","forge_diffusion","forge_validator","forge_packaging","forge_lineage"]
__version__ = "0.1.0-dev"
''',
 "vaultmind_forge/forge_cli.py": None, # will pull from packaged source below
}

# We'll embed the contents from this script's message into files:
files = {
"vaultmind_forge/forge_cli.py": """PASTE_CLI_HERE""",
"vaultmind_forge/forge_agent/agent.py": """PASTE_AGENT_HERE""",
"vaultmind_forge/forge_diffusion/generator.py": """PASTE_GEN_HERE""",
"vaultmind_forge/forge_validator/validator.py": """PASTE_VAL_HERE""",
"vaultmind_forge/forge_packaging/packager.py": """PASTE_PACK_HERE""",
"vaultmind_forge/forge_lineage/lineage.py": """PASTE_LINEAGE_HERE"""
}

# Replace placeholders with the real content. Because sending large blocks inside the file is awkward here,
# best approach: copy the content from the modules provided in the repo message into the placeholders manually,
# or run this script after you pasted the module content into the mapped variables above.
print("Please paste the module sources into this script under `files` map where placeholders are.")
sys.exit(1)
