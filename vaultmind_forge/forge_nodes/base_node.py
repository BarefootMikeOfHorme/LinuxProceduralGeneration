"""
Base Node Classes - Foundation for all node types

Every module in Vaultmind Forge can be exposed as a node:
- forge_diffusion -> SDXL Generator Node
- forge_sr -> Super Resolution Node
- forge_ai -> Merlinv1 Agent Node
- etc.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Type
import uuid


class DataType(str, Enum):
    """Data types that can flow between nodes"""
    # Core types
    IMAGE = "image"          # PIL Image or numpy array
    VIDEO = "video"          # Video file path or frames
    MESH_3D = "mesh_3d"      # 3D mesh (trimesh, etc.)
    TEXT = "text"            # String data
    NUMBER = "number"        # Int or float
    BOOLEAN = "boolean"      # True/False

    # Complex types
    PROMPT = "prompt"        # Structured prompt with metadata
    STYLE = "style"          # Style profile
    PALETTE = "palette"      # Color palette
    ASSET = "asset"          # Generic asset with lineage
    BATCH = "batch"          # List of items

    # Control flow
    SIGNAL = "signal"        # Trigger signal (no data)
    ANY = "any"              # Accepts any type


class NodeCategory(str, Enum):
    """Node categories for organization"""
    INPUT = "input"
    GENERATION = "generation"
    ENHANCEMENT = "enhancement"
    CONTROL = "control"
    AI_AGENT = "ai_agent"
    VALIDATION = "validation"
    PROCESSING = "processing"
    OUTPUT = "output"
    UTILITY = "utility"


@dataclass
class NodeInput:
    """Input port on a node"""
    name: str
    data_type: DataType
    description: str = ""
    default_value: Any = None
    required: bool = True
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    options: Optional[List[str]] = None  # For enum inputs

    # Help system
    tooltip: str = ""
    help_url: str = ""

    # AI suggestions
    ai_default: Optional[Callable] = None  # AI can suggest default

    def validate(self, value: Any) -> tuple[bool, str]:
        """Validate input value"""
        if value is None and self.required:
            return False, f"{self.name} is required"

        if self.min_value is not None and value < self.min_value:
            return False, f"{self.name} must be >= {self.min_value}"

        if self.max_value is not None and value > self.max_value:
            return False, f"{self.name} must be <= {self.max_value}"

        if self.options and value not in self.options:
            return False, f"{self.name} must be one of: {self.options}"

        return True, ""


@dataclass
class NodeOutput:
    """Output port on a node"""
    name: str
    data_type: DataType
    description: str = ""

    # Help system
    tooltip: str = ""


@dataclass
class NodeConnection:
    """Connection between two nodes"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_node: str = ""  # Source node ID
    source_output: str = ""  # Output port name
    target_node: str = ""  # Target node ID
    target_input: str = ""  # Input port name

    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())


@dataclass
class NodeMetadata:
    """Metadata for node documentation and help"""
    display_name: str
    description: str
    category: NodeCategory

    # Documentation
    help_text: str = ""
    tutorial_url: str = ""
    example_workflow: str = ""

    # Keyboard shortcuts (built dynamically)
    shortcuts: Dict[str, str] = field(default_factory=dict)

    # AI control
    ai_controllable: bool = True  # Can AI configure this automatically?
    ai_suggestions_enabled: bool = True

    # Visual
    icon: str = ""
    color: str = "#4A90E2"

    # Version tracking
    version: str = "1.0.0"
    deprecated: bool = False
    deprecation_message: str = ""


class BaseNode(ABC):
    """
    Base class for all nodes in the graph.

    Every forge_* module should extend this to become a usable node.
    """

    # Class-level metadata (override in subclasses)
    METADATA: NodeMetadata = NodeMetadata(
        display_name="Base Node",
        description="Abstract base node",
        category=NodeCategory.UTILITY,
    )

    # Define inputs/outputs (override in subclasses)
    INPUTS: List[NodeInput] = []
    OUTPUTS: List[NodeOutput] = []

    def __init__(self, node_id: Optional[str] = None):
        """
        Initialize node instance.

        Args:
            node_id: Unique identifier (auto-generated if None)
        """
        self.id = node_id or str(uuid.uuid4())
        self.enabled = True
        self.cache_enabled = True
        self.cached_output: Optional[Dict[str, Any]] = None

        # Runtime state
        self.input_values: Dict[str, Any] = {}
        self.output_values: Dict[str, Any] = {}
        self.execution_time_ms: float = 0

        # AI control state
        self.ai_mode = False  # Is AI currently controlling this node?
        self.user_override = False  # Did user manually override AI?

        # Position in graph (for UI)
        self.position = {"x": 0, "y": 0}

        # Error state
        self.last_error: Optional[str] = None

    @abstractmethod
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the node's logic.

        Args:
            inputs: Dictionary mapping input names to values

        Returns:
            Dictionary mapping output names to values

        Raises:
            Exception: If execution fails
        """
        pass

    def validate_inputs(self, inputs: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate all inputs before execution"""
        errors = []

        for input_def in self.INPUTS:
            value = inputs.get(input_def.name)
            valid, error = input_def.validate(value)
            if not valid:
                errors.append(error)

        return len(errors) == 0, errors

    def get_ai_suggestion(self, input_name: str, context: Dict[str, Any]) -> Any:
        """
        Get AI suggestion for input value.

        Args:
            input_name: Name of input to get suggestion for
            context: Context from graph (previous nodes, etc.)

        Returns:
            Suggested value or None
        """
        # Find input definition
        input_def = next((i for i in self.INPUTS if i.name == input_name), None)
        if not input_def or not input_def.ai_default:
            return None

        # Call AI suggestion function
        return input_def.ai_default(context)

    def enable_ai_mode(self):
        """Let AI control this node"""
        self.ai_mode = True
        self.user_override = False

    def disable_ai_mode(self):
        """User takes control"""
        self.ai_mode = False
        self.user_override = True

    def get_help(self) -> Dict[str, Any]:
        """Get help information for this node"""
        return {
            "name": self.METADATA.display_name,
            "description": self.METADATA.description,
            "help_text": self.METADATA.help_text,
            "tutorial_url": self.METADATA.tutorial_url,
            "inputs": [
                {
                    "name": i.name,
                    "type": i.data_type.value,
                    "description": i.description,
                    "tooltip": i.tooltip,
                    "help_url": i.help_url,
                    "required": i.required,
                }
                for i in self.INPUTS
            ],
            "outputs": [
                {
                    "name": o.name,
                    "type": o.data_type.value,
                    "description": o.description,
                    "tooltip": o.tooltip,
                }
                for o in self.OUTPUTS
            ],
            "shortcuts": self.METADATA.shortcuts,
            "ai_controllable": self.METADATA.ai_controllable,
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serialize node to dictionary (for saving workflows)"""
        return {
            "id": self.id,
            "type": self.__class__.__name__,
            "enabled": self.enabled,
            "position": self.position,
            "input_values": self.input_values,
            "ai_mode": self.ai_mode,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> BaseNode:
        """Deserialize node from dictionary"""
        node = cls(node_id=data.get("id"))
        node.enabled = data.get("enabled", True)
        node.position = data.get("position", {"x": 0, "y": 0})
        node.input_values = data.get("input_values", {})
        node.ai_mode = data.get("ai_mode", False)
        return node

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id[:8]}...)"
