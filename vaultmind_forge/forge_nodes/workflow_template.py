"""
Workflow Templates - Pre-built node graphs for common tasks

Templates are enterprise-grade starting points with:
- Pre-configured node graphs
- Sensible defaults
- Built-in help and tutorials
- Best practices embedded
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from pathlib import Path
import json


@dataclass
class WorkflowTemplate:
    """
    A pre-built workflow template.

    Templates include:
    - Nodes and their configuration
    - Connections between nodes
    - Default values
    - Help text and tutorial
    - Example assets
    """

    name: str
    description: str
    category: str  # "anime", "game-asset", "cad", etc.

    # Template content
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    connections: List[Dict[str, Any]] = field(default_factory=list)

    # Documentation
    help_text: str = ""
    tutorial_steps: List[str] = field(default_factory=list)
    example_output_url: str = ""

    # Metadata
    author: str = "Vaultmind Forge"
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    difficulty: str = "beginner"  # beginner, intermediate, advanced

    # Requirements
    required_models: List[str] = field(default_factory=list)  # e.g., ["sdxl", "merlinv1"]
    estimated_time_minutes: int = 5

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "nodes": self.nodes,
            "connections": self.connections,
            "help_text": self.help_text,
            "tutorial_steps": self.tutorial_steps,
            "example_output_url": self.example_output_url,
            "author": self.author,
            "version": self.version,
            "tags": self.tags,
            "difficulty": self.difficulty,
            "required_models": self.required_models,
            "estimated_time_minutes": self.estimated_time_minutes,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> WorkflowTemplate:
        """Deserialize from dictionary"""
        return cls(**data)

    def save(self, path: Path) -> None:
        """Save template to JSON file"""
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: Path) -> WorkflowTemplate:
        """Load template from JSON file"""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


class TemplateManager:
    """
    Manages workflow templates.

    Provides:
    - Built-in templates
    - User custom templates
    - Template discovery
    - Template validation
    """

    def __init__(self, templates_dir: Optional[Path] = None):
        """
        Initialize template manager.

        Args:
            templates_dir: Directory containing template files
        """
        self.templates_dir = templates_dir or Path(__file__).parent / "templates"
        self.templates_dir.mkdir(exist_ok=True, parents=True)

        self._templates: Dict[str, WorkflowTemplate] = {}
        self._load_templates()

    def _load_templates(self) -> None:
        """Load all templates from directory"""
        for template_file in self.templates_dir.glob("*.json"):
            try:
                template = WorkflowTemplate.load(template_file)
                self._templates[template.name] = template
            except Exception as e:
                print(f"Failed to load template {template_file}: {e}")

    def get_template(self, name: str) -> Optional[WorkflowTemplate]:
        """Get template by name"""
        return self._templates.get(name)

    def list_templates(self, category: Optional[str] = None) -> List[WorkflowTemplate]:
        """
        List all templates, optionally filtered by category.

        Args:
            category: Filter by category (e.g., "anime", "game-asset")

        Returns:
            List of matching templates
        """
        templates = list(self._templates.values())

        if category:
            templates = [t for t in templates if t.category == category]

        return sorted(templates, key=lambda t: t.name)

    def create_builtin_templates(self) -> None:
        """Create built-in templates"""

        # Template 1: Anime Character
        anime_character = WorkflowTemplate(
            name="anime_character",
            description="Generate anime-style character artwork with quality checks",
            category="anime",
            help_text="""
            This workflow generates anime-style character art with:
            1. AI-refined prompts (Merlinv1)
            2. SDXL generation with anime preset
            3. Super-resolution upscale
            4. Quality validation
            5. Asset packaging with lineage

            Perfect for: Character concept art, visual novels, anime projects
            """,
            tutorial_steps=[
                "1. Enter character description (e.g., 'warrior princess with silver hair')",
                "2. Click 'Prompt Refiner' to let Merlinv1 enhance your prompt",
                "3. Adjust SDXL parameters if needed (or let AI handle it)",
                "4. Click 'Execute' to run the full pipeline",
                "5. Review quality validation results",
                "6. Download packaged asset with metadata",
            ],
            nodes=[
                {
                    "id": "input_1",
                    "type": "TextInputNode",
                    "position": {"x": 100, "y": 200},
                    "input_values": {
                        "text": "warrior princess with silver hair, anime style"
                    },
                },
                {
                    "id": "refiner_1",
                    "type": "PromptRefinerNode",
                    "position": {"x": 350, "y": 200},
                    "ai_mode": True,
                },
                {
                    "id": "sdxl_1",
                    "type": "SDXLGeneratorNode",
                    "position": {"x": 600, "y": 200},
                    "input_values": {
                        "width": 1024,
                        "height": 1024,
                        "style_preset": "anime",
                    },
                },
                {
                    "id": "sr_1",
                    "type": "SuperResolutionNode",
                    "position": {"x": 850, "y": 200},
                },
                {
                    "id": "validator_1",
                    "type": "QualityValidatorNode",
                    "position": {"x": 850, "y": 400},
                },
                {
                    "id": "packager_1",
                    "type": "AssetPackagerNode",
                    "position": {"x": 1100, "y": 300},
                },
            ],
            connections=[
                {
                    "source_node": "input_1",
                    "source_output": "text",
                    "target_node": "refiner_1",
                    "target_input": "prompt",
                },
                {
                    "source_node": "refiner_1",
                    "source_output": "refined_prompt",
                    "target_node": "sdxl_1",
                    "target_input": "prompt",
                },
                {
                    "source_node": "sdxl_1",
                    "source_output": "image",
                    "target_node": "sr_1",
                    "target_input": "image",
                },
                {
                    "source_node": "sr_1",
                    "source_output": "upscaled_image",
                    "target_node": "validator_1",
                    "target_input": "image",
                },
                {
                    "source_node": "sr_1",
                    "source_output": "upscaled_image",
                    "target_node": "packager_1",
                    "target_input": "image",
                },
                {
                    "source_node": "sdxl_1",
                    "source_output": "metadata",
                    "target_node": "packager_1",
                    "target_input": "metadata",
                },
            ],
            tags=["anime", "character", "art", "beginner-friendly"],
            difficulty="beginner",
            required_models=["sdxl", "merlinv1"],
            estimated_time_minutes=3,
        )

        anime_character.save(self.templates_dir / "anime_character.json")

        # Template 2: Game Asset Pipeline
        game_asset = WorkflowTemplate(
            name="game_asset_pbr",
            description="Generate PBR game-ready 3D assets with full material workflow",
            category="game-asset",
            help_text="""
            Professional game asset pipeline with:
            1. Concept image generation
            2. 3D mesh generation
            3. PBR texture generation
            4. Material validation
            5. Export to Unreal/Unity

            Perfect for: Game development, environment art, prop creation
            """,
            tutorial_steps=[
                "1. Describe the asset (e.g., 'rusty medieval sword')",
                "2. Generate concept art reference",
                "3. AI converts 2D to 3D mesh",
                "4. Generate PBR textures (albedo, normal, roughness, metallic)",
                "5. Validate materials meet PBR standards",
                "6. Export to game engine format",
            ],
            tags=["game-dev", "3d", "pbr", "advanced"],
            difficulty="advanced",
            required_models=["sdxl", "mesh-generator"],
            estimated_time_minutes=10,
        )

        game_asset.save(self.templates_dir / "game_asset_pbr.json")

        print(f"Created {len(self._templates)} built-in templates")


# Convenience functions
def load_template(name: str, manager: Optional[TemplateManager] = None) -> Optional[WorkflowTemplate]:
    """Load a template by name"""
    if manager is None:
        manager = TemplateManager()
    return manager.get_template(name)


def save_template(template: WorkflowTemplate, path: Path) -> None:
    """Save a template to file"""
    template.save(path)
