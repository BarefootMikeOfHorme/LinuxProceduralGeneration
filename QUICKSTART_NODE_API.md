# VaultMind Forge Node.js API - Quick Start Guide

Get up and running with the VaultMind Forge Node.js API layer in 5 minutes.

## Prerequisites

- ✅ Node.js 18+ installed
- ✅ Python 3.10+ with VaultMind Forge installed
- ✅ VaultMind Forge Python backend working

## Step 1: Install Dependencies

```bash
cd C:\Users\Administrator\Desktop\Projects\LPG
npm install
```

This will install:
- express (web framework)
- ajv (JSON schema validation)
- multer (file uploads)
- uuid (ID generation)
- cors, helmet (security)

## Step 2: Start the Server

### Development Mode (auto-reload on file changes)

```bash
npm run dev
```

### Production Mode

```bash
npm start
```

You should see:

```
🚀 VaultMind Forge API Server
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📡 Server running at: http://0.0.0.0:3000
🏥 Health check: http://0.0.0.0:3000/api/health
📖 API docs: http://0.0.0.0:3000/
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Step 3: Test the API

### Browser

Open your browser and visit:
- http://localhost:3000 - API documentation
- http://localhost:3000/api/health - Health check

### cURL

```bash
# Health check
curl http://localhost:3000/api/health

# Get version
curl http://localhost:3000/api/version

# Get status
curl http://localhost:3000/api/status
```

### PowerShell

```powershell
# Health check
Invoke-RestMethod -Uri "http://localhost:3000/api/health"

# Get version
Invoke-RestMethod -Uri "http://localhost:3000/api/version"

# Get status
Invoke-RestMethod -Uri "http://localhost:3000/api/status"
```

## Step 4: Run a Demo

```bash
# Using cURL
curl -X POST http://localhost:3000/api/demo \
  -H "Content-Type: application/json" \
  -d '{"outputDir": "my_demo"}'

# Using PowerShell
Invoke-RestMethod -Uri "http://localhost:3000/api/demo" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"outputDir": "my_demo"}'
```

Check the `my_demo` directory for output files!

## Step 5: Create a Generation Job

```bash
# Using cURL
curl -X POST http://localhost:3000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "outputType": "character",
    "styleTags": ["anime", "cel-shaded"],
    "passes": 3,
    "async": true
  }'

# Using PowerShell
$body = @{
    outputType = "character"
    styleTags = @("anime", "cel-shaded")
    passes = 3
    async = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:3000/api/jobs" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

You'll receive a response with a `jobId`. Save it!

```json
{
  "success": true,
  "message": "Job queued for execution",
  "data": {
    "jobId": "550e8400-e29b-41d4-a716-446655440000",
    "status": "queued",
    "statusUrl": "/api/jobs/550e8400-e29b-41d4-a716-446655440000/status"
  }
}
```

## Step 6: Check Job Status

Replace `{jobId}` with your actual job ID:

```bash
# Using cURL
curl http://localhost:3000/api/jobs/{jobId}/status

# Using PowerShell
Invoke-RestMethod -Uri "http://localhost:3000/api/jobs/{jobId}/status"
```

Job statuses:
- `queued` - Job is waiting to start
- `running` - Job is executing
- `completed` - Job finished successfully
- `failed` - Job encountered an error

## Step 7: Get Job Outputs

Once the job status is `completed`:

```bash
# Using cURL
curl http://localhost:3000/api/jobs/{jobId}/outputs

# Using PowerShell
Invoke-RestMethod -Uri "http://localhost:3000/api/jobs/{jobId}/outputs"
```

## Step 8: Validate Assets

```bash
# Using cURL
curl -X POST http://localhost:3000/api/validate/paths \
  -H "Content-Type: application/json" \
  -d '{
    "paths": [
      "C:\\path\\to\\image1.png",
      "C:\\path\\to\\image2.png"
    ]
  }'

# Using PowerShell
$body = @{
    paths = @(
        "C:\path\to\image1.png",
        "C:\path\to\image2.png"
    )
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:3000/api/validate/paths" `
  -Method POST `
  -ContentType "application/json" `
  -Body $body
```

## Using the Example Client

We've provided a complete example client in JavaScript:

```bash
# Install dependencies (if not already done)
npm install

# Run the complete workflow example
node examples/client-example.js workflow

# Run just the demo
node examples/client-example.js demo

# Check API health
node examples/client-example.js health

# List all jobs
node examples/client-example.js jobs
```

Available commands:
- `workflow` - Run complete workflow (default)
- `demo` - Run demo pipeline
- `validate` - Validate example files
- `health` - Check API health
- `version` - Get API version
- `status` - Get system status
- `jobs` - List all jobs

## Configuration (Optional)

Create a `.env` file for custom configuration:

```bash
# Copy the example
cp .env.example .env

# Edit with your settings
notepad .env  # or your preferred editor
```

Example `.env`:

```env
PORT=3000
HOST=0.0.0.0
NODE_ENV=development
CORS_ORIGIN=*
```

## Common Issues

### Port Already in Use

If port 3000 is already in use:

```bash
# Use a different port
PORT=3001 npm start
```

Or edit your `.env` file:

```env
PORT=3001
```

### Python Not Found

If you get "Python not found" errors:

1. Ensure Python is in your PATH
2. On Windows, you may need to use `python` instead of `python3`
3. Edit `src/pythonBridge.js` line 15 if needed

### File Upload Errors

If file uploads fail:

1. Check file size (max 50MB per file)
2. Ensure file is a valid image format (PNG, JPG, WEBP, etc.)
3. Check that `uploads/temp/` directory is writable

## Next Steps

- 📖 Read the full API documentation: [NODE_API_README.md](NODE_API_README.md)
- 🔧 Explore utility functions in `src/utils.js`
- 🐍 Understand the Python bridge in `src/pythonBridge.js`
- 🎨 Customize handlers in `src/handlers.js`
- 🚀 Deploy to production (see deployment guide in NODE_API_README.md)

## API Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET | `/api/version` | Get Forge version |
| GET | `/api/status` | Get system status |
| POST | `/api/demo` | Run demo pipeline |
| POST | `/api/jobs` | Create generation job |
| POST | `/api/jobs/simple` | Create simple job |
| GET | `/api/jobs` | List all jobs |
| GET | `/api/jobs/:id/status` | Get job status |
| GET | `/api/jobs/:id/outputs` | Get job output files |
| POST | `/api/validate` | Validate uploaded files |
| POST | `/api/validate/paths` | Validate files by path |

## Support

- 📚 Full docs: [NODE_API_README.md](NODE_API_README.md)
- 🐛 Report issues: Check main project documentation
- 💡 Example code: See `examples/client-example.js`

---

**You're ready to go!** 🎉

Start making API requests and building amazing AI-generated assets with VaultMind Forge!
