# Validated Assets

## Purpose
Assets that passed forge_validator quality checks.
Separated into winners and rejected for analysis.

## Directory Structure
```
validated/
├── winners/            # Best scoring variations
│   ├── {job_id}/
│   │   ├── winner.png
│   │   ├── scores.json
│   │   └── lineage.json
│   └── ...
└── rejected/           # Failed quality checks
    ├── analysis/       # Validation reports
    └── suggestions/    # AI improvement suggestions
```

## Winners Storage
**One winner per job:**
```
winners/job-123/
├── winner.png              # Best variation
├── scores.json             # All variation scores
├── lineage.json            # Complete lineage record
└── metadata.json           # Generation settings
```

**scores.json Example:**
```json
{
  "job_id": "job-123",
  "variations": [
    {
      "file": "variation_001.png",
      "score": 0.92,
      "winner": true,
      "metrics": {
        "sharpness": 0.89,
        "anatomy": 0.95,
        "prompt_alignment": 0.91
      }
    },
    {
      "file": "variation_002.png",
      "score": 0.78,
      "winner": false,
      "metrics": {...}
    }
  ]
}
```

## Rejected Storage
**Track why assets failed:**
```
rejected/
├── analysis/
│   └── job-123_variation-002.json
└── suggestions/
    └── job-123_variation-002.json
```

**analysis/job-123_variation-002.json:**
```json
{
  "asset": "generated/diffusion/job-123/variation_002.png",
  "score": 0.78,
  "threshold": 0.85,
  "status": "REJECTED",
  "failed_metrics": [
    {
      "metric": "sharpness",
      "value": 0.72,
      "threshold": 0.75,
      "reason": "Image appears blurry"
    },
    {
      "metric": "anatomy",
      "value": 0.68,
      "threshold": 0.70,
      "reason": "Anatomical errors detected"
    }
  ]
}
```

**suggestions/job-123_variation-002.json:**
```json
{
  "asset": "variation_002.png",
  "suggestions": [
    "Increase resolution or adjust denoising steps for sharper details",
    "Use reference images or anatomy ControlNet to improve anatomical accuracy",
    "Try lower CFG scale (6-7) to reduce artifacts"
  ],
  "retry_settings": {
    "steps": 40,
    "cfg_scale": 6.5,
    "use_controlnet": "anatomy"
  }
}
```

## Usage
1. forge_validator checks all generated variations
2. Winners → `validated/winners/{job_id}/`
3. Rejected → `rejected/` with analysis
4. Use suggestions to improve next generation
5. Winners ready for export to engines
