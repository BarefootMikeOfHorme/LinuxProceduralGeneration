"""
VaultMind Forge - Input Node Executors
Nodes that provide input data to workflows
"""

from typing import Dict, List, Any
from pathlib import Path

from backend.core.base_executor import NodeExecutor, InputSpec, OutputSpec
from backend.core.types import DataType


class TextInputExecutor(NodeExecutor):
    """
    Text Input Node - Provides text data to the workflow.
    """

    @property
    def node_type(self) -> str:
        return "textInput"

    @property
    def display_name(self) -> str:
        return "Text Input"

    @property
    def category(self) -> str:
        return "input"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="text",
                type=DataType.TEXT,
                required=False,
                default="",
                description="Text to output"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="text",
                type=DataType.TEXT,
                description="Text output"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Simply output the input text"""
        text = self.get_input_value(inputs, "text", "")

        return {
            "text": text
        }


class NumberInputExecutor(NodeExecutor):
    """
    Number Input Node - Provides numeric data to the workflow.
    """

    @property
    def node_type(self) -> str:
        return "numberInput"

    @property
    def display_name(self) -> str:
        return "Number Input"

    @property
    def category(self) -> str:
        return "input"

    @property
    def input_spec(self) -> List[InputSpec]:
        return [
            InputSpec(
                name="value",
                type=DataType.NUMBER,
                required=False,
                default=0,
                description="Number to output"
            ),
        ]

    @property
    def output_spec(self) -> List[OutputSpec]:
        return [
            OutputSpec(
                name="value",
                type=DataType.NUMBER,
                description="Number output"
            ),
        ]

    def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Simply output the input number"""
        value = self.get_input_value(inputs, "value", 0)

        # Ensure it's a number
        try:
            value = float(value)
        except (ValueError, TypeError):
            value = 0.0

        return {
            "value": value
        }


if __name__ == "__main__":
    # Test executors
    text_executor = TextInputExecutor()
    print(f"Text Input: {text_executor.node_type}")
    print(f"  Inputs: {[s.name for s in text_executor.input_spec]}")
    print(f"  Outputs: {[s.name for s in text_executor.output_spec]}")

    number_executor = NumberInputExecutor()
    print(f"Number Input: {number_executor.node_type}")
    print(f"  Inputs: {[s.name for s in number_executor.input_spec]}")
    print(f"  Outputs: {[s.name for s in number_executor.output_spec]}")
