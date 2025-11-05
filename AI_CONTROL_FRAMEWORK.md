# AI Control Framework for VaultMind Forge
## Intelligent Autonomous Pipeline with Human-in-Loop

**Created:** 2025-11-04
**Purpose:** Give AI significant control throughout asset pipeline while maintaining quality and human oversight

---

## PHILOSOPHY: AI-First with Smart Escalation

```
AI handles everything it's confident about
↓
Only escalates to human when uncertain
↓
Learns from human corrections
↓
Improves over time
```

**Goal:** 90%+ autonomous operation, 10% human review for edge cases

---

## 1. AI AUTHORITY LEVELS

### Full Autonomous (90-95% automated)
```yaml
Authority: AI decides everything
Human Role: Periodic audits only
Use For:
  - Background assets
  - Texture generation
  - Basic props
  - Batch optimization

Thresholds:
  auto_approve: 0.85
  auto_fix: 0.75
  flag_for_review: 0.60
  auto_reject: 0.40
```

### High Autonomy (80-90% automated)
```yaml
Authority: AI decides most, escalates edge cases
Human Role: Review flagged items
Use For:
  - Standard game assets
  - Environment pieces
  - Generic characters
  - Production workflow

Thresholds:
  auto_approve: 0.90
  auto_fix: 0.80
  flag_for_review: 0.70
  auto_reject: 0.50
```

### Supervised (50-70% automated)
```yaml
Authority: AI suggests, human approves
Human Role: Approve all significant decisions
Use For:
  - Hero assets
  - Main characters
  - Key environments
  - Marketing materials

Thresholds:
  auto_approve: 0.95 (very high bar)
  auto_fix: 0.85
  flag_for_review: 0.80
  auto_reject: 0.60
```

### Advisory Only (0-20% automated)
```yaml
Authority: AI only provides recommendations
Human Role: Makes all decisions
Use For:
  - Critical assets
  - Final approval stage
  - Client deliverables
  - Legal/compliance review
```

---

## 2. AI DECISION POINTS THROUGHOUT PIPELINE

### Stage 1: Generation (forge_diffusion)

#### Decision: Initial Quality Gate
```python
# AI evaluates freshly generated images
def assess_generation_quality(image, prompt, references):
    metrics = {
        "sharpness": compute_laplacian_variance(image),
        "prompt_alignment": clip_similarity(image, prompt),
        "artifact_detection": detect_artifacts_ml(image),
        "color_fidelity": compare_color_distribution(image, references),
        "anatomy_check": check_anatomy_ml(image) if is_character else 1.0
    }

    confidence = ensemble_scoring(metrics)

    if confidence >= 0.85:
        return "APPROVE", confidence, "All metrics strong"
    elif confidence >= 0.60:
        return "FLAG_FOR_REVIEW", confidence, format_concerns(metrics)
    elif confidence >= 0.40:
        return "RETRY", confidence, suggest_adjustments(metrics)
    else:
        return "REJECT", confidence, "Critical failures detected"
```

**AI Authority:** Full Autonomous
- Auto-approves 85%+ confidence
- Auto-retries 40-85% with parameter tweaks
- Auto-rejects <40%
- Human reviews only 5-10% edge cases

#### Decision: Retry Parameter Selection
```python
# AI determines how to fix failed generations
def suggest_retry_parameters(failed_metrics, attempt_history):
    """
    Learned policy for parameter adjustment
    """
    adjustments = {}

    # Pattern recognition from successful retries
    if failed_metrics["sharpness"] < 0.7:
        adjustments = {
            "cfg_scale": current_cfg + 1.0,
            "steps": current_steps + 5,
            "sampler": "more_stable_sampler"
        }

    if failed_metrics["prompt_alignment"] < 0.75:
        adjustments = {
            "cfg_scale": current_cfg + 1.5,
            "prompt": emphasize_keywords(prompt),
            "negative_prompt": add_common_issues(negative)
        }

    # Learn from attempt history
    if attempt_history:
        adjustments = refine_based_on_pattern(adjustments, attempt_history)

    return adjustments, confidence_in_fix
```

**AI Authority:** Full Autonomous
- Automatically adjusts parameters for retries
- Uses learned policy from successful fixes
- Escalates only if 3+ retries fail

#### Decision: Winner Selection
```python
# AI picks best from multiple variations
def select_winner(variations: List[ImageMetrics], context: JobContext):
    """
    Ensemble scoring with contextual weighting
    """
    # Weight metrics based on job type
    if context.output_type == "character":
        weights = {
            "anatomy": 0.25,
            "sharpness": 0.20,
            "prompt_alignment": 0.25,
            "artifact_score": 0.20,
            "consistency": 0.10
        }
    elif context.output_type == "environment":
        weights = {
            "consistency": 0.25,
            "sharpness": 0.20,
            "prompt_alignment": 0.25,
            "color_fidelity": 0.20,
            "artifact_score": 0.10
        }

    scores = [weighted_score(v, weights) for v in variations]
    winner_idx = argmax(scores)

    # Calculate confidence based on score separation
    confidence = score_separation_confidence(scores)

    if confidence >= 0.85:
        return winner_idx, "Auto-selected"
    else:
        return winner_idx, "Flagged - close scores, please review"
```

**AI Authority:** High Autonomy
- Auto-selects 85%+ confidence
- Flags close competitions for human choice

---

### Stage 2: Validation (forge_validator)

#### Decision: Mesh Quality Assessment
```python
# AI validates mesh topology and quality
def validate_mesh(mesh: Mesh, target_engine: str):
    checks = {
        "manifold": check_manifold(mesh),
        "normals": check_normal_consistency(mesh),
        "uvs": check_uv_quality(mesh),
        "triangles": check_triangle_quality(mesh),
        "vertex_count": check_poly_budget(mesh, target_engine)
    }

    # ML-based topology flow scoring
    topology_score = ml_score_topology(mesh)

    # Auto-fix if high confidence
    if checks["manifold"]["fixable"] and checks["manifold"]["confidence"] > 0.90:
        mesh_fixed = auto_fix_manifold(mesh)
        return "FIXED", mesh_fixed, "Auto-repaired non-manifold edges"

    if all_checks_pass(checks) and topology_score > 0.85:
        return "PASS", mesh, "All quality checks passed"
    elif any_critical_failures(checks):
        return "FAIL", mesh, format_failures(checks)
    else:
        return "FLAG", mesh, format_warnings(checks)
```

**AI Authority:** Full Autonomous
- Auto-fixes 90%+ confidence issues
- Auto-passes clean meshes
- Flags ambiguous cases

#### Decision: Texture Quality Assessment
```python
# AI validates texture quality
def validate_texture(texture: Image, texture_type: str):
    checks = {
        "resolution": check_resolution_power_of_two(texture),
        "seams": detect_seams_cv(texture),  # Computer vision
        "compression_artifacts": detect_compression_artifacts(texture),
        "color_space": validate_color_space(texture, texture_type)
    }

    # PBR-specific checks
    if texture_type == "normal":
        checks["normal_validity"] = check_normal_map_validity(texture)
    elif texture_type == "metallic":
        checks["binary_metallic"] = check_metallic_is_binary(texture)

    if all_checks_pass(checks):
        return "PASS", "All texture checks passed"
    elif checks["seams"]["fixable"]:
        return "AUTO_FIX", apply_seam_fix(texture)
    else:
        return "FLAG", format_texture_issues(checks)
```

**AI Authority:** High Autonomy
- Auto-fixes seams if confident
- Auto-passes clean textures
- Flags PBR violations

---

### Stage 3: Optimization (forge_converter)

#### Decision: LOD Generation Strategy
```python
# AI determines LOD configuration
def plan_lod_strategy(mesh: Mesh, usage_context: Dict):
    """
    Context-aware LOD planning
    """
    # Analyze mesh importance
    importance_map = compute_saliency_map(mesh)

    # Determine LOD levels needed
    if usage_context["distance_range"] == "close_only":
        lod_levels = 2  # Minimal LODs
    elif usage_context["distance_range"] == "far_visible":
        lod_levels = 4  # Full LOD chain
    else:
        lod_levels = 3  # Standard

    # Calculate reduction per level
    reductions = []
    for level in range(1, lod_levels):
        # Preserve important areas, aggressively simplify background
        reduction = adaptive_reduction_ml(
            mesh, level, importance_map, usage_context
        )
        reductions.append(reduction)

    # Calculate screen coverage thresholds
    object_radius = compute_bounding_sphere_radius(mesh)
    screen_coverages = [1.0, 0.5, 0.25, 0.1][:lod_levels]

    return {
        "lod_levels": lod_levels,
        "reductions": reductions,
        "screen_coverages": screen_coverages,
        "preserve_silhouette": True,
        "algorithm": "quadric_error"
    }
```

**AI Authority:** Full Autonomous
- Determines LOD configuration automatically
- Adapts to usage context
- No human approval needed for standard assets

#### Decision: Texture Resolution Selection
```python
# AI selects optimal texture resolution per platform
def select_texture_resolution(
    original_texture: Image,
    target_platform: str,
    asset_importance: str
):
    """
    Multi-factor resolution decision
    """
    # Platform constraints
    platform_limits = {
        "desktop_high": 4096,
        "desktop_medium": 2048,
        "mobile_high": 1024,
        "mobile_medium": 512,
        "mobile_low": 256
    }

    # Importance adjustments
    importance_multipliers = {
        "hero": 1.0,      # Full resolution
        "standard": 0.75,  # 75% resolution
        "background": 0.5  # 50% resolution
    }

    # Compute optimal size
    max_size = platform_limits[target_platform]
    importance_mult = importance_multipliers[asset_importance]
    optimal_size = int(max_size * importance_mult)

    # Ensure power of two
    optimal_size = next_power_of_two(optimal_size)

    # Visual quality check
    if would_cause_visible_quality_loss(original_texture, optimal_size):
        # Bump up one level
        optimal_size *= 2

    return optimal_size, f"Selected {optimal_size}x{optimal_size} for {target_platform}/{asset_importance}"
```

**AI Authority:** Full Autonomous
- Automatically selects resolutions
- Balances quality vs performance
- Considers platform and importance

#### Decision: Compression Format Selection
```python
# AI selects optimal compression format
def select_compression_format(
    texture_type: str,
    target_platform: str,
    quality_requirement: str
):
    """
    Smart compression selection
    """
    # Rule-based + learned preferences
    if target_platform in ["desktop", "console"]:
        compression_map = {
            "diffuse": "bc7" if quality_requirement == "high" else "bc1",
            "normal": "bc5",
            "metallic": "bc4",
            "roughness": "bc4",
            "ao": "bc4"
        }
    elif target_platform == "mobile":
        compression_map = {
            "diffuse": "astc",
            "normal": "astc",
            "metallic": "etc2",
            "roughness": "etc2",
            "ao": "etc2"
        }
    elif target_platform == "web":
        compression_map = {
            "diffuse": "basis",  # Universal
            "normal": "basis",
            "metallic": "basis",
            "roughness": "basis",
            "ao": "basis"
        }

    selected = compression_map.get(texture_type, "auto")

    # Validate no quality loss
    if quality_requirement == "lossless":
        selected = "png"  # Override with lossless

    return selected, f"Selected {selected} for {texture_type} on {target_platform}"
```

**AI Authority:** Full Autonomous
- Automatically selects compression
- Platform-aware
- Quality-aware

---

### Stage 4: Conversion (forge_converter)

#### Decision: Format Selection
```python
# AI selects optimal export format
def select_export_format(
    asset_type: str,
    target_engine: str,
    feature_requirements: List[str]
):
    """
    Context-aware format selection
    """
    # Engine preferences
    engine_formats = {
        "unity": {
            "model": "fbx",
            "texture": "png",  # Unity handles import compression
            "material": "mat"
        },
        "unreal": {
            "model": "fbx",
            "texture": "tga",
            "material": "uasset"
        },
        "godot": {
            "model": "gltf",  # Godot prefers GLTF
            "texture": "webp",  # Godot 4.x
            "material": "tres"
        },
        "web": {
            "model": "glb",  # Binary GLTF for web
            "texture": "basis",
            "material": "embedded"
        }
    }

    selected_formats = engine_formats.get(target_engine, {})

    # Feature-based overrides
    if "animations" in feature_requirements and target_engine == "web":
        selected_formats["model"] = "glb"  # GLB supports animations
    if "nanite" in feature_requirements and target_engine == "unreal":
        # Nanite-specific settings
        selected_formats["nanite_settings"] = {
            "single_smoothing_group": True,
            "weighted_normals": True
        }

    return selected_formats
```

**AI Authority:** Full Autonomous
- Automatically selects formats
- Engine-aware
- Feature-aware

#### Decision: Material Conversion Strategy
```python
# AI converts materials between engines
def convert_material(
    source_material: Material,
    target_engine: str,
    source_engine: str
):
    """
    Intelligent material conversion
    """
    # Detect material type
    material_type = classify_material_type_ml(source_material)

    # Map shader model
    if material_type == "pbr_standard":
        if target_engine == "unity":
            shader = "Standard (Metallic)"
        elif target_engine == "unreal":
            shader = "StandardSurface"
        elif target_engine == "godot":
            shader = "StandardMaterial3D"

    # Convert properties
    converted = {}
    for prop, value in source_material.properties.items():
        target_prop = map_property_name(prop, target_engine)
        target_value = convert_property_value(value, prop, target_engine)
        converted[target_prop] = target_value

    # Texture packing differences
    if target_engine == "unreal":
        # Unreal uses ORM (Occlusion, Roughness, Metallic) packing
        converted_textures = pack_orm_textures(
            source_material.textures
        )
    elif target_engine == "unity":
        # Unity uses separate channels
        converted_textures = unpack_to_separate_textures(
            source_material.textures
        )

    return converted, "Material converted successfully"
```

**AI Authority:** Full Autonomous
- Auto-converts materials
- Handles texture packing differences
- Shader model mapping

---

## 3. LEARNING & ADAPTATION

### Feedback Loop
```python
class AILearningSystem:
    def record_human_correction(self, decision_id, ai_decision, human_decision):
        """Store correction for learning"""
        self.corrections.append({
            "decision_id": decision_id,
            "ai_said": ai_decision,
            "human_said": human_decision,
            "context": self.get_decision_context(decision_id),
            "timestamp": now()
        })

        # If 50+ corrections accumulated, suggest retraining
        if len(self.corrections) >= 50:
            self.trigger_retraining_alert()

    def adapt_thresholds(self):
        """Dynamically adjust confidence thresholds"""
        # Analyze performance
        false_positive_rate = self.calculate_false_positives()

        # If >10% false positives, raise approval threshold
        if false_positive_rate > 0.10:
            self.threshold_auto_approve += 0.02
            log(f"Increased approval threshold to {self.threshold_auto_approve}")

        # If <2% false positives and low flag rate, lower threshold
        if false_positive_rate < 0.02 and self.flag_rate < 0.10:
            self.threshold_auto_approve -= 0.01
            log(f"Decreased approval threshold to {self.threshold_auto_approve}")
```

### Performance Monitoring
```python
# Track AI performance metrics
metrics_dashboard = {
    "total_decisions": 10000,
    "auto_approved": 8500,      # 85%
    "flagged_for_review": 1200,  # 12%
    "auto_rejected": 300,        # 3%
    "human_overrides": 150,      # 1.5% of flagged
    "accuracy_rate": 0.93,       # 93% correct when reviewed
    "avg_decision_time_ms": 45,
    "false_positive_rate": 0.04  # 4%
}

# Alert if performance degrades
if metrics_dashboard["false_positive_rate"] > 0.10:
    alert("AI false positive rate high - review needed")
if metrics_dashboard["accuracy_rate"] < 0.85:
    alert("AI accuracy dropped - possible model drift")
```

---

## 4. HUMAN-IN-LOOP CHECKPOINTS

### When AI Escalates to Human

#### Confidence-Based Escalation
```python
# AI automatically flags uncertain decisions
if confidence < threshold_flag:
    escalate_to_human(
        asset=asset,
        ai_recommendation=ai_decision,
        ai_confidence=confidence,
        reasoning=explanation,
        alternatives=[option1, option2, option3]
    )
```

#### Asset Type Requirements
```python
# Policy-based escalation
require_human_approval = [
    "hero_assets",        # Main character, key props
    "character_models",   # All characters
    "final_export",       # Production-ready assets
    "client_deliverables" # External deliverables
]

if asset.type in require_human_approval:
    escalate_to_human(asset, "Policy requires human approval")
```

#### Anomaly Detection
```python
# Statistical anomaly escalation
if is_statistical_outlier(metrics, historical_data):
    escalate_to_human(
        asset=asset,
        reason="Unusual metrics detected",
        anomaly_details=explain_anomaly(metrics)
    )
```

### Human Review Interface
```python
# What humans see when reviewing
review_request = {
    "asset_id": "char_001_diffusion_v3",
    "ai_decision": "APPROVE",
    "ai_confidence": 0.72,  # Below auto-approve threshold
    "ai_reasoning": "Good prompt alignment (0.88) and sharpness (0.81), but anatomy score borderline (0.68)",

    "metrics": {
        "sharpness": 0.81,
        "anatomy": 0.68,      # <-- Flagged
        "prompt_alignment": 0.88,
        "artifact_score": 0.95,
        "overall": 0.72
    },

    "ai_suggestions": [
        {"action": "approve", "reason": "Metrics acceptable for background character"},
        {"action": "retry", "adjustments": {"steps": +10, "cfg": +1.0}, "reason": "Improve anatomy score"},
        {"action": "reject", "reason": "Anatomy critical for character asset"}
    ],

    "preview_image": "path/to/preview.png",
    "comparison_references": ["ref1.png", "ref2.png"]
}

# Human picks: approve, retry with AI suggestions, or reject
human_decision = await wait_for_human_input(review_request)

# AI learns from this
ai.record_feedback(review_request, human_decision)
```

---

## 5. WORKFLOW EXAMPLES

### Example 1: Fully Autonomous Background Asset
```
Input: Generate 20 rock textures for environment

1. forge_diffusion generates 20 textures
   → AI auto-approves 18 (confidence > 0.85)
   → AI auto-retries 2 (confidence 0.60-0.85)
   → Retry generates replacements
   → AI auto-approves both retries

2. forge_validator checks all 20
   → AI auto-passes 19 (all checks OK)
   → AI auto-fixes 1 (minor seam detected, high confidence fix)

3. forge_converter optimizes for mobile
   → AI selects 1024x1024 resolution
   → AI selects ASTC compression
   → AI generates 3 LOD levels

4. Export to Unity
   → AI converts to Unity format
   → AI creates material presets
   → AI generates metadata

Result: 20 production-ready assets, zero human intervention, 100% autonomous
```

### Example 2: Hero Character (Supervised)
```
Input: Generate main character texture

1. forge_diffusion generates 10 variations
   → AI scores all 10
   → AI recommends variation #3 (highest score: 0.89)
   → HUMAN REVIEWS: "I prefer #7 actually"
   → AI learns: variation #7 had score 0.82 (human valued style over metrics)

2. forge_validator checks selected texture
   → AI validates all checks pass
   → AI detects slight seam in arm area (confidence: 0.75)
   → HUMAN REVIEWS: "That seam is acceptable"
   → AI learns: seams in low-visibility areas OK for this asset type

3. forge_converter optimization
   → AI suggests 4K resolution
   → AI suggests BC7 compression
   → HUMAN APPROVES

4. Export to Unreal with Nanite
   → AI prepares Nanite-ready settings
   → AI generates LOD chain
   → HUMAN REVIEWS final export
   → HUMAN APPROVES

Result: 1 hero asset, 4 human checkpoints, AI did 90% of work
```

### Example 3: AI Learns from Correction
```
Iteration 1:
  → AI approves texture with sharpness 0.78
  → Human rejects: "Too blurry for UI element"
  → AI records: UI elements need sharpness > 0.85

Iteration 2:
  → AI flags UI texture with sharpness 0.82
  → Human approves: "This is fine"
  → AI records: Adjusted threshold for UI to 0.82

Iteration 3:
  → AI auto-approves UI texture with sharpness 0.83
  → No human review needed
  → AI learned the correct threshold

Result: AI adapted policy from human feedback
```

---

## 6. IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Immediate)
- [x] AI decision engine core
- [x] Confidence scoring system
- [x] Decision point schemas
- [ ] Feedback recording system
- [ ] Performance monitoring dashboard

### Phase 2: Integration (Week 1)
- [ ] Integrate with forge_diffusion (generation decisions)
- [ ] Integrate with forge_validator (quality decisions)
- [ ] Integrate with forge_converter (optimization decisions)
- [ ] Human review interface (web UI)

### Phase 3: Learning (Week 2)
- [ ] Correction database
- [ ] Threshold adaptation system
- [ ] Pattern recognition for retries
- [ ] Anomaly detection

### Phase 4: Advanced (Week 3-4)
- [ ] ML-based topology scoring
- [ ] Computer vision seam detection
- [ ] Learned parameter adjustment policies
- [ ] Context-aware decision weighting

---

## 7. CONFIGURATION EXAMPLES

### Full Autonomy Config (Background Assets)
```json
{
  "ai_authority_level": "full_autonomous",
  "confidence_thresholds": {
    "auto_approve": 0.85,
    "auto_fix": 0.75,
    "flag_for_review": 0.60,
    "auto_reject": 0.40
  },
  "human_override": {
    "enabled": true,
    "require_approval_for": [],
    "approval_timeout": 0
  },
  "learning_feedback": {
    "adapt_thresholds": true,
    "retrain_trigger": 50
  }
}
```

### Supervised Config (Hero Assets)
```json
{
  "ai_authority_level": "supervised",
  "confidence_thresholds": {
    "auto_approve": 0.95,
    "auto_fix": 0.85,
    "flag_for_review": 0.80,
    "auto_reject": 0.60
  },
  "human_override": {
    "enabled": true,
    "require_approval_for": ["hero_assets", "character_models", "final_export"],
    "approval_timeout": 600
  },
  "learning_feedback": {
    "adapt_thresholds": false,
    "retrain_trigger": 100
  }
}
```

---

## CONCLUSION

The AI Control Framework gives the AI **significant autonomous authority** while maintaining **quality and human oversight**:

✅ **90%+ autonomous** for standard assets
✅ **Smart escalation** when uncertain
✅ **Learns from corrections** to improve
✅ **Transparent reasoning** for every decision
✅ **Performance tracking** to ensure quality
✅ **Flexible authority levels** per asset type

**Result:** AI handles the repetitive work, humans focus on creative decisions and edge cases.

---

**Next Steps:**
1. Implement AIDecisionEngine in forge_validator
2. Add human review UI (web dashboard)
3. Collect initial feedback data (100 decisions)
4. Begin threshold adaptation
5. Expand to forge_converter decisions

**Generated:** 2025-11-04
