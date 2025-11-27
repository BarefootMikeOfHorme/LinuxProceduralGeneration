"""
VaultMind Forge - Node Executor Registry
Centralized registry of all node executors
"""

from typing import Dict, List, Optional
import logging

from .base_executor import NodeExecutor


logger = logging.getLogger(__name__)


class NodeRegistry:
    """
    Registry for all node executors.

    Provides:
    - Registration of node executors
    - Lookup by node type
    - List all available nodes
    - Category-based filtering
    """

    def __init__(self):
        self._executors: Dict[str, NodeExecutor] = {}

    def register(self, executor: NodeExecutor) -> None:
        """
        Register a node executor.

        Args:
            executor: NodeExecutor instance to register

        Raises:
            ValueError: If node type already registered
        """
        node_type = executor.node_type

        if node_type in self._executors:
            raise ValueError(
                f"Node type '{node_type}' is already registered"
            )

        self._executors[node_type] = executor
        logger.info(f"Registered node executor: {node_type}")

    def get_executor(self, node_type: str) -> NodeExecutor:
        """
        Get executor for a node type.

        Args:
            node_type: Type identifier of the node

        Returns:
            NodeExecutor instance

        Raises:
            KeyError: If node type not found
        """
        if node_type not in self._executors:
            raise KeyError(
                f"No executor registered for node type: '{node_type}'\n"
                f"Available types: {list(self._executors.keys())}"
            )

        return self._executors[node_type]

    def has_executor(self, node_type: str) -> bool:
        """Check if executor exists for a node type"""
        return node_type in self._executors

    def list_all(self) -> List[str]:
        """List all registered node types"""
        return list(self._executors.keys())

    def list_by_category(self, category: str) -> List[NodeExecutor]:
        """
        List all executors in a category.

        Args:
            category: Category name (e.g., 'generation', 'processing')

        Returns:
            List of executors in that category
        """
        return [
            executor for executor in self._executors.values()
            if executor.category == category
        ]

    def get_categories(self) -> List[str]:
        """Get list of all unique categories"""
        categories = set(executor.category for executor in self._executors.values())
        return sorted(categories)

    def get_node_info(self, node_type: str) -> Dict:
        """
        Get comprehensive info about a node type.

        Args:
            node_type: Node type identifier

        Returns:
            Dictionary with node information
        """
        executor = self.get_executor(node_type)

        return {
            "type": executor.node_type,
            "displayName": executor.display_name,
            "category": executor.category,
            "inputs": [
                {
                    "name": spec.name,
                    "type": spec.type.value,
                    "required": spec.required,
                    "default": spec.default,
                    "description": spec.description,
                }
                for spec in executor.input_spec
            ],
            "outputs": [
                {
                    "name": spec.name,
                    "type": spec.type.value,
                    "description": spec.description,
                }
                for spec in executor.output_spec
            ],
        }

    def count(self) -> int:
        """Get total number of registered executors"""
        return len(self._executors)

    def __repr__(self):
        return f"<NodeRegistry count={self.count()}>"


def create_default_registry() -> NodeRegistry:
    """
    Create and populate registry with all default node executors.

    Returns:
        NodeRegistry with all executors registered
    """
    registry = NodeRegistry()

    # Import and register all executor modules
    from backend.executors.input_nodes import TextInputExecutor, NumberInputExecutor
    from backend.executors.generation_nodes import SDXLGeneratorExecutor
    from backend.executors.processing_nodes import SuperResolutionExecutor
    from backend.executors.ai_nodes import PromptRefinerExecutor

    # Register input nodes
    registry.register(TextInputExecutor())
    registry.register(NumberInputExecutor())

    # Register generation nodes
    registry.register(SDXLGeneratorExecutor())

    # Register processing nodes
    registry.register(SuperResolutionExecutor())

    # Register AI nodes
    registry.register(PromptRefinerExecutor())

    logger.info(f"Created default registry with {registry.count()} executors")
    return registry


if __name__ == "__main__":
    registry = create_default_registry()
    print(f"Node Registry: {registry.count()} executors")
    print(f"Categories: {registry.get_categories()}")
