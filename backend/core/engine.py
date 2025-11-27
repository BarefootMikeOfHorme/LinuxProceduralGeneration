"""
VaultMind Forge - Node Execution Engine
Type-safe workflow execution with DAG topological sorting
"""

from graphlib import TopologicalSorter, CycleError
from typing import Dict, List, Any, Optional
import logging

from .types import DataType, can_connect
from .base_executor import NodeExecutor
from .registry import NodeRegistry


logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when workflow validation fails"""
    pass


class ExecutionError(Exception):
    """Raised when node execution fails"""
    pass


class NodeExecutionEngine:
    """
    Core execution engine for VaultMind Forge workflows.

    Features:
    - Type-safe connection validation
    - DAG topological sorting for correct execution order
    - Output caching (nodes only execute once)
    - Handle-based data flow (sourceHandle → targetHandle)
    - Comprehensive error reporting
    """

    def __init__(self, registry: NodeRegistry):
        """
        Initialize the execution engine.

        Args:
            registry: NodeRegistry containing all available node executors
        """
        self.registry = registry
        self.node_outputs: Dict[str, Dict[str, Any]] = {}
        self.execution_order: List[str] = []

    def execute_workflow(self, workflow) -> Dict[str, Dict[str, Any]]:
        """
        Execute a complete workflow.

        Args:
            workflow: Workflow object with nodes and connections

        Returns:
            Dictionary of node outputs: {node_id: {handle_name: data}}

        Raises:
            ValidationError: If workflow validation fails
            ExecutionError: If node execution fails
        """
        logger.info(f"Starting workflow execution with {len(workflow.nodes)} nodes")

        # Reset state
        self.node_outputs = {}
        self.execution_order = []

        # 1. Validate workflow
        self.validate_workflow(workflow)

        # 2. Build execution order (topological sort)
        self.execution_order = self.build_execution_order(workflow)
        logger.info(f"Execution order: {self.execution_order}")

        # 3. Execute nodes in order
        for node_id in self.execution_order:
            node = self.find_node(workflow, node_id)
            self.execute_node(node, workflow)

        logger.info(f"Workflow execution completed successfully")
        return self.node_outputs

    def validate_workflow(self, workflow) -> None:
        """
        Validate entire workflow for type safety and correctness.

        Args:
            workflow: Workflow to validate

        Raises:
            ValidationError: If validation fails
        """
        errors = []

        # Validate all nodes exist in registry
        for node in workflow.nodes:
            if not self.registry.has_executor(node.type):
                errors.append(f"Unknown node type: '{node.type}' (node {node.id})")

        # Validate all connections
        for conn in workflow.connections:
            try:
                self.validate_connection(conn, workflow)
            except ValidationError as e:
                errors.append(str(e))

        if errors:
            error_msg = "Workflow validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
            raise ValidationError(error_msg)

    def validate_connection(self, conn, workflow) -> None:
        """
        Validate a single connection for type safety.

        Args:
            conn: Connection to validate
            workflow: Workflow containing the connection

        Raises:
            ValidationError: If connection is invalid
        """
        # Find source and target nodes
        source_node = self.find_node(workflow, conn.source)
        target_node = self.find_node(workflow, conn.target)

        if not source_node:
            raise ValidationError(f"Connection source node not found: {conn.source}")

        if not target_node:
            raise ValidationError(f"Connection target node not found: {conn.target}")

        # Get executors
        source_executor = self.registry.get_executor(source_node.type)
        target_executor = self.registry.get_executor(target_node.type)

        # Find output spec for source handle
        source_output = source_executor.get_output_handle(conn.sourceHandle)
        if not source_output:
            raise ValidationError(
                f"Node '{source_node.type}' (id: {conn.source}) "
                f"has no output handle '{conn.sourceHandle}'"
            )

        # Find input spec for target handle
        target_input = target_executor.get_input_handle(conn.targetHandle)
        if not target_input:
            raise ValidationError(
                f"Node '{target_node.type}' (id: {conn.target}) "
                f"has no input handle '{conn.targetHandle}'"
            )

        # Check type compatibility
        if not can_connect(source_output.type, target_input.type):
            raise ValidationError(
                f"Type mismatch: Cannot connect {source_output.type.value} to {target_input.type.value}\n"
                f"  Source: {source_node.type}.{conn.sourceHandle} (id: {conn.source})\n"
                f"  Target: {target_node.type}.{conn.targetHandle} (id: {conn.target})"
            )

    def build_execution_order(self, workflow) -> List[str]:
        """
        Build execution order using topological sort.

        Args:
            workflow: Workflow to sort

        Returns:
            List of node IDs in execution order

        Raises:
            ValidationError: If workflow contains cycles
        """
        ts = TopologicalSorter()

        # Build dependency graph
        for node in workflow.nodes:
            dependencies = []

            # Find all nodes that this node depends on
            for conn in workflow.connections:
                if conn.target == node.id:
                    dependencies.append(conn.source)

            # Add node with its dependencies
            ts.add(node.id, *dependencies)

        # Get execution order
        try:
            return list(ts.static_order())
        except CycleError as e:
            raise ValidationError(f"Workflow contains circular dependencies: {e}")

    def execute_node(self, node, workflow) -> None:
        """
        Execute a single node.

        Args:
            node: Node to execute
            workflow: Workflow containing the node

        Raises:
            ExecutionError: If execution fails
        """
        logger.info(f"Executing node: {node.type} (id: {node.id})")

        try:
            # Get executor for this node type
            executor = self.registry.get_executor(node.type)

            # Build inputs from connections + node data
            inputs = self.build_node_inputs(node, workflow)

            # Validate inputs
            executor.validate_inputs(inputs)

            # Execute node
            outputs = executor.execute(inputs)

            # Validate outputs contain expected handles
            for output_spec in executor.output_spec:
                if output_spec.name not in outputs:
                    logger.warning(
                        f"Node {node.type} (id: {node.id}) did not produce "
                        f"expected output '{output_spec.name}'"
                    )

            # Cache outputs
            self.node_outputs[node.id] = outputs

            logger.info(f"  ✓ Completed: {list(outputs.keys())}")

        except Exception as e:
            error_msg = f"Node execution failed: {node.type} (id: {node.id})\n  Error: {e}"
            logger.error(error_msg)
            import traceback
            traceback.print_exc()
            raise ExecutionError(error_msg) from e

    def build_node_inputs(self, node, workflow) -> Dict[str, Any]:
        """
        Build input dictionary for a node from connections and node data.

        Args:
            node: Node to build inputs for
            workflow: Workflow containing connections

        Returns:
            Dictionary of inputs keyed by handle names
        """
        inputs = {}

        # Start with node's own data (default values)
        inputs.update(node.data)

        # Override with connected inputs (handle-based matching)
        for conn in workflow.connections:
            if conn.target == node.id:
                # Get upstream node's output
                if conn.source not in self.node_outputs:
                    # This shouldn't happen if topological sort worked
                    logger.warning(
                        f"Source node {conn.source} has no outputs yet "
                        f"(executing {node.id})"
                    )
                    continue

                source_outputs = self.node_outputs[conn.source]

                # Match handles: sourceHandle → targetHandle
                if conn.sourceHandle in source_outputs:
                    inputs[conn.targetHandle] = source_outputs[conn.sourceHandle]
                    logger.debug(
                        f"  Connected: {conn.source}.{conn.sourceHandle} → "
                        f"{node.id}.{conn.targetHandle}"
                    )
                else:
                    logger.warning(
                        f"Source node {conn.source} has no output handle "
                        f"'{conn.sourceHandle}'"
                    )

        return inputs

    def find_node(self, workflow, node_id: str):
        """Find a node by ID in the workflow"""
        for node in workflow.nodes:
            if node.id == node_id:
                return node
        return None

    def get_node_output(self, node_id: str, handle: str = None) -> Any:
        """
        Get output from a specific node.

        Args:
            node_id: ID of the node
            handle: Output handle name (if None, returns all outputs)

        Returns:
            Output data or None if not found
        """
        if node_id not in self.node_outputs:
            return None

        outputs = self.node_outputs[node_id]

        if handle is None:
            return outputs

        return outputs.get(handle)

    def clear_cache(self) -> None:
        """Clear cached outputs (for re-execution)"""
        self.node_outputs = {}
        self.execution_order = []


if __name__ == "__main__":
    print("NodeExecutionEngine loaded")
    print("Features:")
    print("  - Type-safe validation")
    print("  - DAG topological sorting")
    print("  - Output caching")
    print("  - Handle-based data flow")
