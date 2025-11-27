"""
VaultMind Forge - Node Executor Base Classes
Defines the pattern for implementing node executors
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from .types import DataType


@dataclass
class InputSpec:
    """Specification for a node input"""
    name: str
    type: DataType
    required: bool = True
    default: Any = None
    description: str = ""

    def validate(self, value: Any) -> bool:
        """Validate if a value is acceptable for this input"""
        if value is None:
            return not self.required
        # Type validation would go here (basic check for now)
        return True


@dataclass
class OutputSpec:
    """Specification for a node output"""
    name: str
    type: DataType
    description: str = ""


class NodeExecutor(ABC):
    """
    Base class for all node executors.

    Each node type must implement a NodeExecutor subclass that:
    1. Defines input/output specifications
    2. Implements the execute() method
    3. Returns outputs keyed by output handle names
    """

    @property
    @abstractmethod
    def node_type(self) -> str:
        """Unique identifier for this node type (e.g., 'sdxlGenerator')"""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable name (e.g., 'SDXL Generator')"""
        pass

    @property
    @abstractmethod
    def category(self) -> str:
        """Node category (e.g., 'generation', 'processing', 'input')"""
        pass

    @property
    @abstractmethod
    def input_spec(self) -> List[InputSpec]:
        """List of input specifications"""
        pass

    @property
    @abstractmethod
    def output_spec(self) -> List[OutputSpec]:
        """List of output specifications"""
        pass

    @abstractmethod
    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the node's operation.

        Args:
            inputs: Dictionary of input values keyed by input handle names

        Returns:
            Dictionary of output values keyed by output handle names

        Raises:
            ValueError: If required inputs are missing or invalid
            RuntimeError: If execution fails
        """
        pass

    def validate_inputs(self, inputs: Dict[str, Any]) -> None:
        """
        Validate that all required inputs are present and valid.

        Args:
            inputs: Input dictionary to validate

        Raises:
            ValueError: If validation fails
        """
        for spec in self.input_spec:
            if spec.required and spec.name not in inputs:
                raise ValueError(
                    f"Node '{self.node_type}' missing required input '{spec.name}'"
                )

            if spec.name in inputs:
                value = inputs[spec.name]
                if not spec.validate(value):
                    raise ValueError(
                        f"Node '{self.node_type}' input '{spec.name}' validation failed"
                    )

    def get_input_value(self, inputs: Dict[str, Any], name: str, default: Any = None) -> Any:
        """
        Safely get an input value with fallback to spec default.

        Args:
            inputs: Input dictionary
            name: Input name
            default: Override default (if not provided, uses spec default)

        Returns:
            Input value or default
        """
        if name in inputs:
            return inputs[name]

        # Find spec for this input
        spec = next((s for s in self.input_spec if s.name == name), None)
        if spec:
            return default if default is not None else spec.default

        return default

    def get_input_handle(self, name: str) -> Optional[InputSpec]:
        """Get input specification by handle name"""
        return next((spec for spec in self.input_spec if spec.name == name), None)

    def get_output_handle(self, name: str) -> Optional[OutputSpec]:
        """Get output specification by handle name"""
        return next((spec for spec in self.output_spec if spec.name == name), None)

    def __repr__(self):
        return f"<{self.__class__.__name__} type='{self.node_type}'>"


class PassthroughExecutor(NodeExecutor):
    """
    Base class for nodes that pass data through without modification.
    Useful for utility nodes like Preview, Reroute, etc.
    """

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Default: pass all inputs as outputs"""
        return inputs


if __name__ == "__main__":
    # Example usage
    print("NodeExecutor base classes loaded")
    print(f"InputSpec: {InputSpec.__annotations__}")
    print(f"OutputSpec: {OutputSpec.__annotations__}")
