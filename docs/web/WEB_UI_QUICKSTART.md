# VaultMind Forge - Web UI Quick Start

**Get the web interface running in 2 minutes**

---

## Step 1: Start the API Server (30 seconds)

```bash
cd C:\Users\Administrator\Desktop\Projects\LPG
npm start
```

**Expected output:**
```
🔥 VaultMind Forge API Server
================================
✅ Server started on http://localhost:5084
✅ Python CLI: Available
✅ Web UI: http://localhost:5084/web/index.html
```

---

## Step 2: Open Web UI (10 seconds)

Open your browser and go to:

```
http://localhost:5084/web/index.html
```

You should see:
- 🔥 VaultMind Forge header
- Status indicator (connecting...)
- 5 specialist agents listed on left
- Generation workspace in center

---

## Step 3: Test Connection (15 seconds)

1. Click **⚙️ Settings** button (top right)
2. Click **Test Connection** button
3. You should see: ✅ "Connected to VaultMind Forge API"
4. Close settings panel

---

## Step 4: Generate Your First Asset (60 seconds)

1. In the **Generation Prompt** box, enter:
   ```
   a photorealistic cyberpunk samurai warrior, neon city background, dramatic lighting, highly detailed
   ```

2. Keep default parameters:
   - Width: 1024
   - Height: 1024
   - Steps: 30
   - Batch Size: 1
   - Output Type: Character

3. Click **🚀 Generate Asset**

4. Wait for generation (will use placeholder mode if SDXL not installed)

5. Results appear in grid below

---

## Alternative: Python CLI Fallback

If Node.js is not available or you prefer terminal:

```bash
python vaultmind_cli.py generate \
    "a photorealistic cyberpunk samurai warrior" \
    --width 1024 \
    --height 1024 \
    --steps 30 \
    --output smoke_test.png
```

**Why Python CLI?**
- Primary interface for Linux servers
- Rich terminal UI with colors/progress bars
- No browser required
- Scriptable for automation

---

## Troubleshooting

### "Connection failed"

**Check if server is running:**
```bash
curl http://localhost:5084/api/health
```

**Expected:** `{"status":"ok"}`

**If not running:**
```bash
cd C:\Users\Administrator\Desktop\Projects\LPG
npm start
```

### "Generation failed"

**Check Python backend:**
```bash
python vaultmind_cli.py --version
```

**If working:** Server will use placeholder mode (1x1 pixel images for testing)

**To install SDXL models:** See main README.md

### Web UI won't load

**Check static file serving:**
```bash
curl http://localhost:5084/web/index.html | head -20
```

**Should return:** HTML starting with `<!DOCTYPE html>`

---

## Next Steps

1. **Configure cloud backend** (Hugging Face, NVIDIA, Replicate)
   - Open Settings → Select backend → Enter API key

2. **View lineage**
   - Click **Lineage** tab to see generation history

3. **Monitor agents**
   - Watch agent dashboard (left panel) during generation

4. **Explore workflows** (coming soon)
   - Click **Workflows** tab

5. **Use Python CLI** for scripting
   ```bash
   python vaultmind_cli.py --help
   ```

---

## Quick Reference

**Web UI URL:** `http://localhost:5084/web/index.html`

**API Health:** `http://localhost:5084/api/health`

**Python CLI:** `python vaultmind_cli.py --help`

**Documentation:** `web/README.md`

---

**That's it! You're ready to generate AI assets. 🎨**
