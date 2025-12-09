# Error Handling Documentation

VaultMind Forge uses structured error responses to help users understand and fix issues quickly.

## Error Response Format

All errors return a consistent JSON structure:

```json
{
  "error": "Short Error Title",
  "message": "Detailed explanation of what went wrong",
  "error_code": "MACHINE_READABLE_CODE",
  "recovery_steps": [
    "Step 1: First thing to try",
    "Step 2: Second thing to try",
    "Step 3: Where to get help"
  ],
  "documentation_url": "/docs/relevant-topic",
  "details": {
    "additional": "context",
    "specific": "to this error"
  }
}
```

## Error Codes

### Authentication & Authorization
- `AUTH_MISSING_API_KEY` - API key not provided in request
- `AUTH_INVALID_API_KEY` - API key is incorrect

### Rate Limiting
- `RATE_LIMIT_EXCEEDED` - Too many requests in time window

### Workflow Errors
- `WORKFLOW_NOT_FOUND` - Workflow ID doesn't exist
- `WORKFLOW_VALIDATION_ERROR` - Workflow structure is invalid
- `WORKFLOW_EXECUTION_ERROR` - Workflow execution failed
- `WORKFLOW_SAVE_ERROR` - Failed to save workflow

### Node Errors
- `NODE_NOT_FOUND` - Node type doesn't exist
- `NODE_MISSING_INPUT` - Required input not provided
- `NODE_INVALID_CONFIG` - Node configuration is invalid
- `NODE_EXECUTION_FAILED` - Node execution error

### File System Errors
- `FILE_NOT_FOUND` - File doesn't exist
- `FILE_ACCESS_DENIED` - Permission denied to access file/directory
- `FILE_INVALID_PATH` - Path is malformed or contains invalid characters

### Execution Errors
- `EXECUTION_NOT_FOUND` - Execution ID doesn't exist
- `EXECUTION_TIMEOUT` - Execution took too long
- `EXECUTION_GPU_ERROR` - GPU-related error

### System Errors
- `DATABASE_ERROR` - Database operation failed
- `INTERNAL_ERROR` - Unexpected server error
- `SERVICE_UNAVAILABLE` - Service is temporarily down

## Example Error Responses

### Workflow Not Found

**Request:**
```bash
GET /api/workflows/abc123
```

**Response:** `404 Not Found`
```json
{
  "error": "Workflow Not Found",
  "message": "Workflow with ID 'abc123' does not exist.",
  "error_code": "WORKFLOW_NOT_FOUND",
  "recovery_steps": [
    "Check that the workflow ID is correct",
    "Verify the workflow wasn't deleted",
    "List all workflows: GET /api/workflows",
    "Create a new workflow if needed: POST /api/workflows"
  ],
  "documentation_url": "/docs/workflows",
  "details": {
    "workflow_id": "abc123"
  }
}
```

### Workflow Validation Error

**Request:**
```bash
POST /api/execute
{
  "nodes": [...],
  "connections": [...]
}
```

**Response:** `400 Bad Request`
```json
{
  "error": "Workflow Validation Failed",
  "message": "Node 'sdxl_generate_1' is missing required input 'prompt'",
  "error_code": "WORKFLOW_VALIDATION_ERROR",
  "recovery_steps": [
    "Fix configuration for node: sdxl_generate_1",
    "Check that all nodes have required inputs connected",
    "Verify all node configurations are complete",
    "Ensure there are no circular dependencies in the workflow",
    "Review workflow structure in the visual editor"
  ],
  "documentation_url": "/docs/workflow-validation",
  "details": {
    "node_id": "sdxl_generate_1"
  }
}
```

### File Access Denied

**Request:**
```bash
GET /api/filesystem/browse?path=C:/Windows/System32
```

**Response:** `403 Forbidden`
```json
{
  "error": "Access Denied",
  "message": "You don't have permission to access 'C:/Windows/System32'.",
  "error_code": "FILE_ACCESS_DENIED",
  "recovery_steps": [
    "Verify the path is within allowed directories (Home, Desktop, Documents, Pictures, Downloads)",
    "Check file/directory permissions",
    "Contact your system administrator if you need access to restricted locations",
    "Try browsing from an allowed root directory"
  ],
  "details": {
    "file_path": "C:/Windows/System32"
  }
}
```

### Rate Limit Exceeded

**Request:**
```bash
POST /api/execute  (6th request in same minute)
```

**Response:** `429 Too Many Requests`
```json
{
  "error": "Rate Limit Exceeded",
  "message": "You've exceeded the rate limit of 5/minute. Please wait before trying again.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "recovery_steps": [
    "Wait 42 seconds before retrying",
    "Reduce the frequency of your requests",
    "Consider upgrading to a higher tier for increased limits",
    "Contact support if you need custom rate limits"
  ],
  "details": {
    "limit": "5/minute",
    "retry_after_seconds": 42
  }
}
```

### GPU Error

**Request:**
```bash
POST /api/execute  (workflow with SDXL node)
```

**Response:** `500 Internal Server Error`
```json
{
  "error": "GPU Error",
  "message": "GPU execution failed: CUDA out of memory",
  "error_code": "EXECUTION_GPU_ERROR",
  "recovery_steps": [
    "Check that CUDA/GPU drivers are installed correctly",
    "Verify GPU is not being used by another process",
    "Try reducing batch size or image resolution",
    "Restart the server to clear GPU memory",
    "Check GPU temperature and power settings"
  ],
  "documentation_url": "/docs/gpu-troubleshooting",
  "details": {
    "gpu_error": "CUDA out of memory"
  }
}
```

## Best Practices for API Clients

### 1. Check error_code First

Always check the `error_code` field for programmatic error handling:

```javascript
try {
  const response = await fetch('/api/workflows/123');
  const data = await response.json();
} catch (error) {
  if (error.error_code === 'WORKFLOW_NOT_FOUND') {
    // Handle workflow not found
  } else if (error.error_code === 'RATE_LIMIT_EXCEEDED') {
    // Implement retry with backoff
  }
}
```

### 2. Display recovery_steps to Users

Show recovery steps in your UI to help users fix issues themselves:

```javascript
if (error.recovery_steps) {
  showErrorDialog({
    title: error.error,
    message: error.message,
    steps: error.recovery_steps
  });
}
```

### 3. Log Full Error for Debugging

Log the complete error object for troubleshooting:

```javascript
console.error('API Error:', {
  code: error.error_code,
  message: error.message,
  details: error.details,
  timestamp: new Date().toISOString()
});
```

### 4. Implement Retry Logic for Specific Errors

Some errors are transient and worth retrying:

```javascript
const RETRYABLE_ERRORS = [
  'RATE_LIMIT_EXCEEDED',
  'SERVICE_UNAVAILABLE',
  'DATABASE_ERROR'
];

if (RETRYABLE_ERRORS.includes(error.error_code)) {
  const retryAfter = error.details?.retry_after_seconds || 5;
  setTimeout(() => retryRequest(), retryAfter * 1000);
}
```

## HTTP Status Code Mapping

| Status Code | Meaning | Common Error Codes |
|-------------|---------|-------------------|
| 400 | Bad Request | WORKFLOW_VALIDATION_ERROR, NODE_INVALID_CONFIG |
| 401 | Unauthorized | AUTH_MISSING_API_KEY |
| 403 | Forbidden | AUTH_INVALID_API_KEY, FILE_ACCESS_DENIED |
| 404 | Not Found | WORKFLOW_NOT_FOUND, FILE_NOT_FOUND, EXECUTION_NOT_FOUND |
| 429 | Too Many Requests | RATE_LIMIT_EXCEEDED |
| 500 | Internal Server Error | WORKFLOW_EXECUTION_ERROR, GPU_ERROR, DATABASE_ERROR, INTERNAL_ERROR |
| 503 | Service Unavailable | SERVICE_UNAVAILABLE |

## Support

If you encounter an error that:
- Has unclear recovery steps
- Persists after following recovery steps
- Shouldn't have occurred based on your usage

Please report it with:
1. The full error response JSON
2. What you were doing when it occurred
3. Timestamp and error_code
4. Relevant log files from `./logs/`
