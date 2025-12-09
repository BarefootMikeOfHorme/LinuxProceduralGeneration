"""
VaultMind Forge - Error Handling System
Provides structured error responses with recovery steps for better UX
"""

from typing import List, Optional, Dict, Any
from enum import Enum
from fastapi import HTTPException
from pydantic import BaseModel


class ErrorCode(str, Enum):
    """Standard error codes for the API"""

    # Authentication & Authorization
    AUTH_MISSING_API_KEY = "AUTH_MISSING_API_KEY"
    AUTH_INVALID_API_KEY = "AUTH_INVALID_API_KEY"

    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # Workflow Errors
    WORKFLOW_NOT_FOUND = "WORKFLOW_NOT_FOUND"
    WORKFLOW_VALIDATION_ERROR = "WORKFLOW_VALIDATION_ERROR"
    WORKFLOW_EXECUTION_ERROR = "WORKFLOW_EXECUTION_ERROR"
    WORKFLOW_SAVE_ERROR = "WORKFLOW_SAVE_ERROR"

    # Node Errors
    NODE_NOT_FOUND = "NODE_NOT_FOUND"
    NODE_MISSING_INPUT = "NODE_MISSING_INPUT"
    NODE_INVALID_CONFIG = "NODE_INVALID_CONFIG"
    NODE_EXECUTION_FAILED = "NODE_EXECUTION_FAILED"

    # File System Errors
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_ACCESS_DENIED = "FILE_ACCESS_DENIED"
    FILE_INVALID_PATH = "FILE_INVALID_PATH"

    # Execution Errors
    EXECUTION_NOT_FOUND = "EXECUTION_NOT_FOUND"
    EXECUTION_TIMEOUT = "EXECUTION_TIMEOUT"
    EXECUTION_GPU_ERROR = "EXECUTION_GPU_ERROR"

    # System Errors
    DATABASE_ERROR = "DATABASE_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


class ErrorDetail(BaseModel):
    """Structured error response"""

    error: str  # Short error title
    message: str  # Detailed error message
    error_code: ErrorCode  # Machine-readable error code
    recovery_steps: List[str]  # Steps user can take to fix
    documentation_url: Optional[str] = None  # Link to docs
    details: Optional[Dict[str, Any]] = None  # Additional context


class VaultMindError(Exception):
    """Base exception for VaultMind errors with structured details"""

    def __init__(
        self,
        error: str,
        message: str,
        error_code: ErrorCode,
        recovery_steps: List[str],
        status_code: int = 500,
        documentation_url: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.error = error
        self.message = message
        self.error_code = error_code
        self.recovery_steps = recovery_steps
        self.status_code = status_code
        self.documentation_url = documentation_url
        self.details = details or {}
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        return {
            "error": self.error,
            "message": self.message,
            "error_code": self.error_code.value,
            "recovery_steps": self.recovery_steps,
            "documentation_url": self.documentation_url,
            "details": self.details
        }

    def to_http_exception(self) -> HTTPException:
        """Convert to FastAPI HTTPException"""
        return HTTPException(
            status_code=self.status_code,
            detail=self.to_dict()
        )


# ============================================================================
# Pre-defined Error Factories
# ============================================================================

def workflow_not_found_error(workflow_id: str) -> VaultMindError:
    """Workflow not found in database"""
    return VaultMindError(
        error="Workflow Not Found",
        message=f"Workflow with ID '{workflow_id}' does not exist.",
        error_code=ErrorCode.WORKFLOW_NOT_FOUND,
        status_code=404,
        recovery_steps=[
            "Check that the workflow ID is correct",
            "Verify the workflow wasn't deleted",
            "List all workflows: GET /api/workflows",
            "Create a new workflow if needed: POST /api/workflows"
        ],
        documentation_url="/docs/workflows",
        details={"workflow_id": workflow_id}
    )


def workflow_validation_error(validation_message: str, node_id: Optional[str] = None) -> VaultMindError:
    """Workflow failed validation"""
    recovery_steps = [
        "Check that all nodes have required inputs connected",
        "Verify all node configurations are complete",
        "Ensure there are no circular dependencies in the workflow",
        "Review workflow structure in the visual editor"
    ]

    if node_id:
        recovery_steps.insert(0, f"Fix configuration for node: {node_id}")

    return VaultMindError(
        error="Workflow Validation Failed",
        message=validation_message,
        error_code=ErrorCode.WORKFLOW_VALIDATION_ERROR,
        status_code=400,
        recovery_steps=recovery_steps,
        documentation_url="/docs/workflow-validation",
        details={"node_id": node_id} if node_id else {}
    )


def workflow_execution_error(execution_message: str, node_id: Optional[str] = None) -> VaultMindError:
    """Workflow execution failed"""
    recovery_steps = [
        "Check the execution logs for detailed error information",
        "Verify all input files exist and are accessible",
        "Ensure you have sufficient disk space and memory",
        "Try running the workflow again",
        "Simplify the workflow to isolate the failing node"
    ]

    if node_id:
        recovery_steps.insert(0, f"Check node '{node_id}' configuration and inputs")

    return VaultMindError(
        error="Workflow Execution Failed",
        message=execution_message,
        error_code=ErrorCode.WORKFLOW_EXECUTION_ERROR,
        status_code=500,
        recovery_steps=recovery_steps,
        documentation_url="/docs/troubleshooting",
        details={"node_id": node_id} if node_id else {}
    )


def node_missing_input_error(node_id: str, input_name: str) -> VaultMindError:
    """Node is missing a required input"""
    return VaultMindError(
        error="Node Missing Required Input",
        message=f"Node '{node_id}' is missing required input '{input_name}'.",
        error_code=ErrorCode.NODE_MISSING_INPUT,
        status_code=400,
        recovery_steps=[
            f"Connect a node output to the '{input_name}' input on node '{node_id}'",
            "Check that the connected node executed successfully",
            "Verify the input type matches what's expected",
            "Review the node documentation for input requirements"
        ],
        documentation_url=f"/docs/nodes/{node_id}",
        details={"node_id": node_id, "input_name": input_name}
    )


def file_not_found_error(file_path: str) -> VaultMindError:
    """File not found at specified path"""
    return VaultMindError(
        error="File Not Found",
        message=f"The file '{file_path}' does not exist or is not accessible.",
        error_code=ErrorCode.FILE_NOT_FOUND,
        status_code=404,
        recovery_steps=[
            "Check that the file path is correct",
            "Verify the file hasn't been moved or deleted",
            "Ensure you have permission to access this location",
            "Use the file browser to locate the file: GET /api/filesystem/browse"
        ],
        details={"file_path": file_path}
    )


def file_access_denied_error(file_path: str) -> VaultMindError:
    """Access denied to file or directory"""
    return VaultMindError(
        error="Access Denied",
        message=f"You don't have permission to access '{file_path}'.",
        error_code=ErrorCode.FILE_ACCESS_DENIED,
        status_code=403,
        recovery_steps=[
            "Verify the path is within allowed directories (Home, Desktop, Documents, Pictures, Downloads)",
            "Check file/directory permissions",
            "Contact your system administrator if you need access to restricted locations",
            "Try browsing from an allowed root directory"
        ],
        details={"file_path": file_path}
    )


def execution_not_found_error(execution_id: str) -> VaultMindError:
    """Execution not found"""
    return VaultMindError(
        error="Execution Not Found",
        message=f"Execution with ID '{execution_id}' does not exist.",
        error_code=ErrorCode.EXECUTION_NOT_FOUND,
        status_code=404,
        recovery_steps=[
            "Check that the execution ID is correct",
            "The execution may have expired or been cleaned up",
            "Start a new workflow execution: POST /api/execute"
        ],
        details={"execution_id": execution_id}
    )


def rate_limit_exceeded_error(limit: str, retry_after: int) -> VaultMindError:
    """Rate limit exceeded"""
    return VaultMindError(
        error="Rate Limit Exceeded",
        message=f"You've exceeded the rate limit of {limit}. Please wait before trying again.",
        error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
        status_code=429,
        recovery_steps=[
            f"Wait {retry_after} seconds before retrying",
            "Reduce the frequency of your requests",
            "Consider upgrading to a higher tier for increased limits",
            "Contact support if you need custom rate limits"
        ],
        details={"limit": limit, "retry_after_seconds": retry_after}
    )


def gpu_error(error_message: str) -> VaultMindError:
    """GPU execution error"""
    return VaultMindError(
        error="GPU Error",
        message=f"GPU execution failed: {error_message}",
        error_code=ErrorCode.EXECUTION_GPU_ERROR,
        status_code=500,
        recovery_steps=[
            "Check that CUDA/GPU drivers are installed correctly",
            "Verify GPU is not being used by another process",
            "Try reducing batch size or image resolution",
            "Restart the server to clear GPU memory",
            "Check GPU temperature and power settings"
        ],
        documentation_url="/docs/gpu-troubleshooting",
        details={"gpu_error": error_message}
    )


def database_error(operation: str, error_message: str) -> VaultMindError:
    """Database operation failed"""
    return VaultMindError(
        error="Database Error",
        message=f"Database {operation} failed: {error_message}",
        error_code=ErrorCode.DATABASE_ERROR,
        status_code=500,
        recovery_steps=[
            "Try the operation again",
            "Check disk space is available",
            "Verify database file permissions",
            "Contact support if the problem persists",
            "Check logs for detailed error information"
        ],
        details={"operation": operation, "db_error": error_message}
    )


def internal_error(error_message: str) -> VaultMindError:
    """Internal server error"""
    return VaultMindError(
        error="Internal Server Error",
        message=f"An unexpected error occurred: {error_message}",
        error_code=ErrorCode.INTERNAL_ERROR,
        status_code=500,
        recovery_steps=[
            "Try the operation again",
            "Check the server logs for more details",
            "Report this error to support with the error message",
            "Include the timestamp and what you were doing when the error occurred"
        ],
        details={"error": error_message}
    )


__all__ = [
    "ErrorCode",
    "ErrorDetail",
    "VaultMindError",
    "workflow_not_found_error",
    "workflow_validation_error",
    "workflow_execution_error",
    "node_missing_input_error",
    "file_not_found_error",
    "file_access_denied_error",
    "execution_not_found_error",
    "rate_limit_exceeded_error",
    "gpu_error",
    "database_error",
    "internal_error",
]
