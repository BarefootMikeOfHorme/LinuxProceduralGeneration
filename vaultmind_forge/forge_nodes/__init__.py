"""
Vaultmind Forge - Node Graph System
Enterprise-grade visual workflow editor for AI content generation
"""

from .base_node import (
    BaseNode,
    NodeInput,
    NodeOutput,
    NodeConnection,
    NodeCategory,
    DataType,
)

from .node_graph import (
    NodeGraph,
    GraphExecutor,
    ExecutionResult,
)

from .node_registry import (
    NodeRegistry,
    register_node,
    get_node_class,
    list_nodes,
)

from .workflow_template import (
    WorkflowTemplate,
    TemplateManager,
    load_template,
    save_template,
)

__all__ = [
    # Core
    "BaseNode",
    "NodeInput",
    "NodeOutput",
    "NodeConnection",
    "NodeCategory",
    "DataType",
    # Graph
    "NodeGraph",
    "GraphExecutor",
    "ExecutionResult",
    # Registry
    "NodeRegistry",
    "register_node",
    "get_node_class",
    "list_nodes",
    # Templates
    "WorkflowTemplate",
    "TemplateManager",
    "load_template",
    "save_template",
]

__version__ = "1.0.0"
