# VaultMind Forge - Complete Component Inventory

**Generated**: Automatically scanned codebase
**Purpose**: Definitive reference of all modules, classes, and functions

---

## __init__

### `vaultmind_forge.__init__`

**Exports** (`__all__`):
- `forge_ai`
- `forge_agent`
- `forge_agents`
- `forge_diffusion`
- `forge_3d`
- `forge_video`
- `forge_procedural`
- `forge_intake`
- `forge_converter`
- `forge_batch`
- `forge_sr`
- `forge_semantic`
- `forge_validator`
- `forge_executor`
- `forge_bots`
- `forge_monitor`
- `forge_packaging`
- `forge_lineage`
- `forge_versioning`
- `forge_cli`
- `cli`

**Functions**:
- `get_all_modules()`

---

## cli

### `vaultmind_forge.cli`

**Exports** (`__all__`):
- `VaultMindCLI`
- `AgentManager`
- `WorkflowVisualizer`
- `ProcessOrchestrator`
- `StatsMonitor`

---

### `vaultmind_forge.cli.agent_manager`

**Classes**:
- `AgentStatus`
- `AgentType`
- `AgentPriority`
- `Agent`
- `AgentManager`

**Functions**:
- `to_dict()`
- `list_agents()`
- `get_agent()`
- `get_agent_implementation()`
- `invoke_agent()`
- `update_agent_status()`
- `show_dashboard()`
- `show_agent_details()`
- `manage_agent_interactive()`
- `get_stats()`
- `export_state()`

---

### `vaultmind_forge.cli.agent_network`

**Classes**:
- `MessageType`
- `MessagePriority`
- `AgentMessage`
- `AgentProposal`
- `CollaborativeTask`
- `AgentNetwork`

**Functions**:
- `to_dict()`
- `vote()`
- `share_knowledge()`
- `get_knowledge()`
- `create_agent_team()`
- `visualize_network()`
- `get_stats()`

---

### `vaultmind_forge.cli.checkpoint_manager`

**Classes**:
- `CheckpointType`
- `RecoveryStrategy`
- `CheckpointMetadata`
- `CheckpointData`
- `CheckpointManager`

**Functions**:
- `to_dict()`
- `from_dict()`
- `list_checkpoints()`
- `get_latest_checkpoint()`
- `visualize_checkpoint_history()`

---

### `vaultmind_forge.cli.constants`

**Exports** (`__all__`):
- `MAX_PARALLEL_TASKS`
- `CHECKPOINT_INTERVAL_SECONDS`
- `DAG_POLL_INTERVAL_SECONDS`
- `DEFAULT_TASK_TIMEOUT`
- `GENERATION_TASK_TIMEOUT`
- `VALIDATION_TASK_TIMEOUT`
- `ENHANCEMENT_TASK_TIMEOUT`
- `AGENT_QUALITY_GUARDIAN_AUTONOMY`
- `AGENT_PROMPT_REFINER_AUTONOMY`
- `AGENT_PARAMETER_OPTIMIZER_AUTONOMY`
- `AGENT_MATERIAL_SPECIALIST_AUTONOMY`
- `AGENT_RESOLUTION_EXPERT_AUTONOMY`
- `CONFIDENCE_THRESHOLD_AUTO_APPROVE`
- `CONFIDENCE_THRESHOLD_AUTO_FIX`
- `CONFIDENCE_THRESHOLD_FLAG_REVIEW`
- `CONFIDENCE_THRESHOLD_AUTO_REJECT`
- `QUALITY_GUARDIAN_MIN_CONFIDENCE`
- `QUALITY_GUARDIAN_AUTO_FIX_CONFIDENCE`
- `MONITOR_REFRESH_INTERVAL_SECONDS`
- `STATS_UPDATE_INTERVAL_SECONDS`
- `GPU_POLL_INTERVAL_SECONDS`
- `DEFAULT_WORKER_COUNT`
- `MAX_WORKER_COUNT`
- `WORKER_HEALTH_CHECK_INTERVAL`
- `WORKER_TIMEOUT_SECONDS`
- `TASK_QUEUE_MAX_SIZE`
- `TASK_BATCH_SIZE`
- `TASK_RETRY_MAX_ATTEMPTS`
- `TASK_RETRY_DELAY_SECONDS`
- `CHECKPOINT_AUTO_SAVE_INTERVAL`
- `CHECKPOINT_MAX_HISTORY`
- `MAX_RETRIES_DEFAULT`
- `RETRY_BACKOFF_BASE`
- `MAX_RETRY_DELAY`
- `CLI_VERSION`
- `MIN_PYTHON_VERSION`
- `MIN_NODE_VERSION`

---

### `vaultmind_forge.cli.distributed_executor`

**Classes**:
- `WorkerStatus`
- `WorkerType`
- `LoadBalancingStrategy`
- `WorkerMetrics`
- `Worker`
- `TaskQueueItem`
- `DistributedExecutor`

**Functions**:
- `update_task_completion()`
- `success_rate()`
- `efficiency_score()`
- `can_handle_task()`
- `load_score()`
- `get_stats()`
- `visualize_workers()`

---

### `vaultmind_forge.cli.multi_modal_pipeline`

**Classes**:
- `Modality`
- `ModalQuality`
- `ModalSpec`
- `ModalResult`
- `PipelineResult`
- `MultiModalPipeline`

**Functions**:
- `visualize_pipeline()`

---

### `vaultmind_forge.cli.process_orchestrator`

**Classes**:
- `ProcessType`
- `ProcessStatus`
- `ProcessResult`
- `ManagedProcess`
- `ProcessOrchestrator`

**Functions**:
- `duration()`
- `to_dict()`
- `execute_python()`
- `execute_rust()`
- `execute_cpp()`
- `execute_nodejs()`
- `execute_with_json_io()`
- `list_processes()`
- `get_process()`
- `show_process_dashboard()`
- `get_stats()`
- `export_state()`

---

### `vaultmind_forge.cli.stats_monitor`

**Classes**:
- `StatsMonitor`

**Functions**:
- `get_system_stats()`
- `get_gpu_stats()`
- `get_nvidia_smi_stats()`
- `display_dashboard()`
- `export_stats()`

---

### `vaultmind_forge.cli.task_decomposer`

**Classes**:
- `TaskComplexity`
- `TaskContext`
- `DecompositionResult`
- `IntelligentTaskDecomposer`

**Functions**:
- `visualize_decomposition()`
- `learn_from_execution()`

---

### `vaultmind_forge.cli.terminal_ui`

**Classes**:
- `TerminalUI`
- `CommandHistory`

**Functions**:
- `header()`
- `success()`
- `error()`
- `warning()`
- `info()`
- `loading()`
- `progress_bar()`
- `table()`
- `panel()`
- `rule()`
- `clear()`
- `print()`
- `prompt()`
- `confirm()`
- `choice()`
- `format_status()`
- `format_time_ago()`
- `display_progress_bar()`
- `wait_for_key()`
- `add()`
- `previous()`
- `next()`
- `last()`
- `all()`

---

### `vaultmind_forge.cli.workflow_engine`

**Classes**:
- `TaskStatus`
- `TaskType`
- `Task`
- `Workflow`
- `WorkflowEngine`

**Functions**:
- `duration()`
- `is_ready()`
- `to_dict()`
- `add_task()`
- `remove_task()`
- `get_ready_tasks()`
- `get_entry_tasks()`
- `get_exit_tasks()`
- `validate_dag()`
- `estimate_duration()`
- `to_dict()`
- `create_workflow()`
- `add_task_to_workflow()`
- `load_checkpoint()`
- `visualize_workflow()`
- `longest_path()`
- `print_task_tree()`

---

## config

### `vaultmind_forge.config`

**Exports** (`__all__`):
- `VaultMindConfig`
- `PathConfig`
- `RuntimeConfig`
- `AIControlConfig`
- `get_config`
- `reload_config`
- `PROJECT_ROOT`
- `CONFIG_DIR`

**Classes**:
- `PathConfig`
- `RuntimeConfig`
- `AIControlConfig`
- `LoggingConfig`
- `VaultMindConfig`

**Functions**:
- `load_json_config()`
- `load_yaml_config()`
- `get_config()`
- `reload_config()`
- `from_preset()`
- `get_model_path()`
- `load_ai_preset()`
- `get_preset_names()`

---

## examples

### `vaultmind_forge.examples.bot_deployment_example`

**Functions**:
- `example_1_asset_monitor()`
- `example_2_qa_bot()`
- `example_3_optimizer_bot()`
- `example_4_lineage_bot()`
- `example_5_full_deployment()`
- `main()`

---

## forge_3d

### `vaultmind_forge.forge_3d`

**Exports** (`__all__`):
- `MeshGenerator`
- `MeshGenerationConfig`
- `MeshGenerationResult`
- `MeshGenerationStage`

---

### `vaultmind_forge.forge_3d.mesh_generator`

**Classes**:
- `MeshGenerationStage`
- `MeshGenerationConfig`
- `MeshGenerationResult`
- `MeshGenerator`
- `PlaceholderInferAPI`

**Functions**:
- `initialize()`
- `generate()`
- `clear_cache()`
- `genStage1()`
- `genStage2()`
- `genStage3()`
- `genStage4()`

---

## forge_agent

### `vaultmind_forge.forge_agent`

**Exports** (`__all__`):
- `JobConfig`
- `JobTemplate`
- `OutputType`
- `RenderStyle`
- `QualityPreset`
- `ColorSpace`
- `AspectRatio`
- `StyleConstraints`
- `ValidationRequirements`
- `GenerationParams`
- `LineageConfig`
- `Reference`
- `ANIME_CHARACTER_TEMPLATE`
- `CONCEPT_ART_TEMPLATE`
- `PIXEL_ART_TEMPLATE`
- `ENVIRONMENT_TEMPLATE`
- `JobPlanner`
- `GenerationPlan`
- `HelperPass`
- `StylePreset`
- `get_style_preset`
- `list_presets_by_style`
- `enhance_prompt_with_style`
- `ANIME_STYLES`
- `REALISTIC_STYLES`
- `ARTISTIC_STYLES`
- `STYLIZED_STYLES`
- `SCIFI_STYLES`
- `ALL_STYLES`

---

### `vaultmind_forge.forge_agent.agent`

**Classes**:
- `GenerationJob`
- `Planner`

**Functions**:
- `plan_simple_job()`

---

### `vaultmind_forge.forge_agent.planner`

**Classes**:
- `HelperPass`
- `GenerationPlan`
- `JobPlanner`

**Functions**:
- `to_dict()`
- `create_plan()`
- `create_simple_job()`
- `create_batch_jobs()`

---

### `vaultmind_forge.forge_agent.schemas`

**Classes**:
- `OutputType`
- `RenderStyle`
- `QualityPreset`
- `ColorSpace`
- `AspectRatio`
- `StyleConstraints`
- `ValidationRequirements`
- `Reference`
- `LineageConfig`
- `GenerationParams`
- `JobConfig`
- `JobTemplate`

**Functions**:
- `ratio()`
- `validate_style_tags()`
- `validate_passes()`
- `to_dict()`
- `from_dict()`
- `create_job()`

---

### `vaultmind_forge.forge_agent.styles`

**Classes**:
- `StylePreset`

**Functions**:
- `get_style_preset()`
- `list_presets_by_style()`
- `enhance_prompt_with_style()`

---

## forge_agents

### `vaultmind_forge.forge_agents`

**Exports** (`__all__`):
- `BaseAgent`
- `AgentDecision`
- `AgentCapability`
- `EscalationReason`
- `QualityGuardianAgent`
- `QualityIssue`
- `QualityDecision`
- `AutoFixType`
- `QualityReport`
- `StyleProfile`
- `ParameterRange`
- `ALL_PROFILES`
- `get_profile`
- `StyleProfileManager`
- `create_style_aware_pipeline`
- `quick_style_detection`
- `get_recommended_params`
- `PromptRefinerAgent`
- `PromptRefinement`
- `ParameterOptimizerAgent`
- `ParameterOptimization`
- `MaterialSuggesterAgent`
- `MaterialSuggestion`
- `MaterialComplexity`
- `TextureType`
- `ResolutionAdvisorAgent`
- `ResolutionRecommendation`
- `Platform`
- `AssetImportance`
- `ResolutionMethod`

---

### `vaultmind_forge.forge_agents.base_agent`

**Classes**:
- `AgentCapability`
- `EscalationReason`
- `AgentDecision`
- `AgentMetrics`
- `BaseAgent`

**Functions**:
- `to_dict()`
- `to_dict()`
- `make_decision()`
- `calculate_confidence()`
- `should_escalate()`
- `record_decision()`
- `learn_from_feedback()`
- `get_metrics()`
- `save_metrics()`
- `load_metrics()`
- `reset_metrics()`
- `get_status()`

---

### `vaultmind_forge.forge_agents.material_suggester`

**Classes**:
- `MaterialComplexity`
- `TextureType`
- `MaterialSuggestion`
- `EngineMaterialSetup`
- `MaterialSuggesterAgent`

**Functions**:
- `suggest_material()`
- `make_decision()`
- `calculate_confidence()`

---

### `vaultmind_forge.forge_agents.parameter_optimizer`

**Classes**:
- `ParameterOptimization`
- `ParameterOptimizerAgent`

**Functions**:
- `optimize_parameters()`
- `make_decision()`
- `calculate_confidence()`

---

### `vaultmind_forge.forge_agents.prompt_refiner`

**Classes**:
- `PromptRefinement`
- `PromptRefinerAgent`

**Functions**:
- `refine_prompt()`
- `make_decision()`
- `calculate_confidence()`

---

### `vaultmind_forge.forge_agents.quality_guardian`

**Classes**:
- `AutoFixType`
- `QualityIssue`
- `QualityDecision`
- `QualityReport`
- `QualityGuardianAgent`

**Functions**:
- `to_dict()`
- `assess_and_fix()`
- `make_decision()`
- `calculate_confidence()`
- `get_fix_effectiveness_report()`
- `get_quality_trends()`

---

### `vaultmind_forge.forge_agents.resolution_advisor`

**Classes**:
- `Platform`
- `AssetImportance`
- `ResolutionMethod`
- `ResolutionRecommendation`
- `ResolutionAdvisorAgent`

**Functions**:
- `recommend_resolution()`
- `make_decision()`
- `calculate_confidence()`

---

### `vaultmind_forge.forge_agents.style_profile_manager`

**Classes**:
- `StyleProfileManager`

**Functions**:
- `create_style_aware_pipeline()`
- `quick_style_detection()`
- `get_recommended_params()`
- `detect_style()`
- `get_optimized_params()`
- `integrate_with_quality_guardian()`
- `create_style_aware_guardian()`
- `enhance_prompt()`
- `get_negative_prompt()`
- `validate_params_for_style()`
- `get_profile_for_prompt()`

---

### `vaultmind_forge.forge_agents.style_profiles`

**Classes**:
- `StyleCategory`
- `ParameterRange`
- `StyleProfile`

**Functions**:
- `get_profile()`
- `list_profiles()`
- `list_categories()`
- `validate()`

---

## forge_ai

### `vaultmind_forge.forge_ai`

**Exports** (`__all__`):
- `BaseAI`
- `AIBackend`
- `AIRequest`
- `AIResponse`
- `AIError`
- `AIManager`
- `create_ai_manager`
- `ModelManager`
- `ModelConfig`
- `ModelRole`
- `ModelState`
- `ModelStatus`
- `create_flux_loader`
- `create_gpt_loader`
- `create_unloader`
- `GPTPlannerBackend`
- `DCFTBackend`
- `Merlinv1Backend`
- `TieredAIManager`
- `TaskComplexity`
- `create_tiered_ai_manager`

---

### `vaultmind_forge.forge_ai.ai_manager`

**Classes**:
- `AIManager`

**Functions**:
- `create_ai_manager()`
- `initialize()`
- `generate()`
- `get_stats()`
- `shutdown()`

---

### `vaultmind_forge.forge_ai.base_ai`

**Classes**:
- `AIBackend`
- `AIRequest`
- `AIResponse`
- `AIError`
- `BaseAI`

**Functions**:
- `initialize()`
- `generate()`
- `is_available()`
- `get_stats()`
- `shutdown()`

---

### `vaultmind_forge.forge_ai.claude_backend`

**Classes**:
- `ClaudeBackend`

**Functions**:
- `initialize()`
- `generate()`
- `is_available()`

---

### `vaultmind_forge.forge_ai.dcft_backend`

**Classes**:
- `DCFTBackend`

**Functions**:
- `initialize()`
- `generate()`
- `is_available()`
- `shutdown()`
- `get_model_stats()`
- `load_dcft()`

---

### `vaultmind_forge.forge_ai.gpt_planner_backend`

**Classes**:
- `GPTPlannerBackend`

**Functions**:
- `initialize()`
- `generate()`
- `is_available()`
- `shutdown()`
- `get_model_stats()`

---

### `vaultmind_forge.forge_ai.huggingface_backend`

**Classes**:
- `HuggingFaceBackend`

**Functions**:
- `initialize()`
- `generate()`
- `is_available()`

---

### `vaultmind_forge.forge_ai.lmstudio_backend`

**Classes**:
- `LMStudioBackend`

**Functions**:
- `initialize()`
- `generate()`
- `is_available()`
- `shutdown()`

---

### `vaultmind_forge.forge_ai.merlinv1_backend`

**Classes**:
- `Merlinv1Backend`

**Functions**:
- `initialize()`
- `generate()`
- `is_available()`
- `shutdown()`

---

### `vaultmind_forge.forge_ai.model_manager`

**Classes**:
- `ModelRole`
- `ModelState`
- `ModelConfig`
- `ModelStatus`
- `ModelManager`
- `_ModelContext`

**Functions**:
- `create_flux_loader()`
- `create_gpt_loader()`
- `create_unloader()`
- `register_model()`
- `load_model()`
- `unload_model()`
- `use_model()`
- `get_model_status()`
- `get_total_memory_usage()`
- `get_loaded_models()`
- `get_stats()`
- `shutdown()`
- `load_flux()`
- `load_gpt()`
- `unload()`
- `unload_worker()`

---

### `vaultmind_forge.forge_ai.ollama_backend`

**Classes**:
- `OllamaBackend`

**Functions**:
- `initialize()`
- `generate()`
- `is_available()`

---

### `vaultmind_forge.forge_ai.openai_backend`

**Classes**:
- `OpenAIBackend`

**Functions**:
- `initialize()`
- `generate()`
- `is_available()`

---

### `vaultmind_forge.forge_ai.tiered_ai_manager`

**Classes**:
- `TaskComplexity`
- `TieredAIManager`

**Functions**:
- `create_tiered_ai_manager()`
- `initialize()`
- `generate()`
- `get_stats()`
- `shutdown()`

---

### `vaultmind_forge.forge_ai.unified_agent_backend`

**Classes**:
- `UnifiedAgentBackend`

**Functions**:
- `initialize()`
- `generate()`
- `is_available()`
- `shutdown()`
- `get_model_stats()`
- `load_unified_agent()`

---

## forge_ascii_art

### `vaultmind_forge.forge_ascii_art`

**Functions**:
- `print_logo()`
- `print_status_banner()`
- `print_success_banner()`
- `print_error_banner()`
- `print_warning_banner()`
- `print_info_banner()`
- `get_data_flow_animation()`
- `print_workflow_progress()`

---

## forge_batch

### `vaultmind_forge.forge_batch`

**Exports** (`__all__`):
- `JobQueue`
- `BatchJob`
- `JobPriority`
- `JobStatus`
- `ResourceManager`
- `ResourceRequirements`
- `GPUStatus`
- `SystemResources`
- `BatchProcessor`
- `WorkerStatus`
- `BatchProgress`

---

### `vaultmind_forge.forge_batch.batch_processor`

**Classes**:
- `WorkerStatus`
- `BatchProgress`
- `BatchProcessor`

**Functions**:
- `submit_job()`
- `submit_batch()`
- `start()`
- `stop()`
- `add_progress_callback()`
- `get_job_status()`
- `get_job()`
- `list_jobs()`
- `get_batch_progress()`
- `is_batch_complete()`
- `wait_for_job()`
- `wait_for_batch()`
- `get_stats()`
- `get_worker_status()`
- `print_status()`
- `cancel_job()`
- `clear_completed()`

---

### `vaultmind_forge.forge_batch.job_queue`

**Classes**:
- `JobPriority`
- `JobStatus`
- `BatchJob`
- `JobQueue`

**Functions**:
- `to_dict()`
- `from_dict()`
- `is_ready_to_run()`
- `calculate_priority_score()`
- `submit()`
- `submit_batch()`
- `get_next_ready_job()`
- `mark_running()`
- `mark_completed()`
- `mark_failed()`
- `cancel_job()`
- `get_job()`
- `list_jobs()`
- `get_queue_depth()`
- `get_running_count()`
- `get_stats()`
- `save()`
- `load()`
- `clear_completed()`

---

### `vaultmind_forge.forge_batch.resource_manager`

**Classes**:
- `ResourceRequirements`
- `GPUStatus`
- `SystemResources`
- `ResourceManager`

**Functions**:
- `get_gpu_count()`
- `get_gpu_status()`
- `get_all_gpu_status()`
- `get_system_resources()`
- `can_allocate()`
- `allocate_gpu()`
- `allocate_resources()`
- `release_resources()`
- `estimate_requirements()`
- `check_system_health()`
- `get_resource_summary()`

---

## forge_bots

### `vaultmind_forge.forge_bots`

**Exports** (`__all__`):
- `BaseBot`
- `BotStatus`
- `BotPriority`
- `BotConfig`
- `AssetMonitorBot`
- `FolderWatchConfig`
- `QualityAssuranceBot`
- `QAConfig`
- `QAReport`
- `ResourceOptimizerBot`
- `OptimizerConfig`
- `LineageInspectorBot`
- `LineageConfig`
- `BotScheduler`
- `ScheduleConfig`

---

### `vaultmind_forge.forge_bots.base_bot`

**Classes**:
- `BotStatus`
- `BotPriority`
- `BotConfig`
- `BotMetrics`
- `BaseBot`

**Functions**:
- `to_dict()`
- `execute_action()`
- `before_cycle()`
- `after_cycle()`
- `start()`
- `stop()`
- `pause()`
- `resume()`
- `create_alert()`
- `clear_alerts()`
- `get_status()`
- `get_metrics()`
- `print_status()`
- `export_metrics()`

---

### `vaultmind_forge.forge_bots.lineage_bot`

**Classes**:
- `LineageConfig`
- `LineageInspectorBot`

**Functions**:
- `execute_action()`
- `get_lineage_status()`
- `print_status()`

---

### `vaultmind_forge.forge_bots.monitor_bot`

**Classes**:
- `FolderWatchConfig`
- `AssetMonitorBot`

**Functions**:
- `main()`
- `execute_action()`
- `add_watch_folder()`
- `remove_watch_folder()`
- `get_watch_status()`
- `print_status()`

---

### `vaultmind_forge.forge_bots.native_bridge`

**Classes**:
- `NativeBridge`

**Functions**:
- `get_native_bridge()`
- `reset_native_bridge()`
- `fast_sharpness_check()`
- `fast_color_fidelity()`
- `comprehensive_validation()`
- `generate_noise_texture()`
- `generate_heightmap()`
- `generate_seed_variations()`
- `get_capabilities()`
- `get_backend_info()`

---

### `vaultmind_forge.forge_bots.optimizer_bot`

**Classes**:
- `OptimizerConfig`
- `ResourceOptimizerBot`

**Functions**:
- `execute_action()`
- `get_optimizer_status()`
- `print_status()`

---

### `vaultmind_forge.forge_bots.qa_bot`

**Classes**:
- `QAConfig`
- `QAReport`
- `QualityAssuranceBot`

**Functions**:
- `to_dict()`
- `execute_action()`
- `get_qa_status()`
- `print_status()`

---

### `vaultmind_forge.forge_bots.scheduler`

**Classes**:
- `BotType`
- `ScheduleConfig`
- `BotScheduler`

**Functions**:
- `deploy_bot()`
- `start_all()`
- `stop_all()`
- `start_bot()`
- `stop_bot()`
- `pause_bot()`
- `resume_bot()`
- `remove_bot()`
- `run_health_check()`
- `get_aggregate_metrics()`
- `export_metrics()`
- `print_dashboard()`
- `save_configuration()`
- `load_configuration()`

---

## forge_cli

### `vaultmind_forge.forge_cli`

**Classes**:
- `NodeData`
- `Connection`
- `WorkflowRequest`

**Functions**:
- `main_callback()`
- `version()`
- `logo()`
- `monitor()`
- `generate()`
- `workflow()`
- `validate()`
- `evaluate()`

---

### `vaultmind_forge.forge_cli.html_report`

**Functions**:
- `write_html_report()`

---

## forge_converter

### `vaultmind_forge.forge_converter`

**Exports** (`__all__`):
- `ConversionProfile`
- `TargetEngine`
- `AssetType`

**Classes**:
- `ConversionProfile`
- `TargetEngine`
- `AssetType`

**Functions**:
- `get_supported_engines()`
- `get_supported_profiles()`
- `get_module_info()`

---

### `vaultmind_forge.forge_converter.ai_control`

**Classes**:
- `AuthorityLevel`
- `DecisionOutcome`
- `Decision`
- `QualityMetrics`
- `AIDecisionEngine`

**Functions**:
- `to_dict()`
- `assess_quality()`
- `suggest_parameter_adjustments()`
- `select_best_variation()`
- `record_human_feedback()`
- `adapt_thresholds()`
- `get_performance_summary()`
- `export_decisions()`

---

### `vaultmind_forge.forge_converter.converter`

**Classes**:
- `ConversionOptions`
- `ConversionResult`
- `AssetConverter`

**Functions**:
- `main()`
- `to_dict()`
- `convert()`
- `batch_convert()`
- `convert_project()`

---

### `vaultmind_forge.forge_converter.engines.__init__`

**Exports** (`__all__`):
- `EngineStructureBuilder`

---

### `vaultmind_forge.forge_converter.engines.structure_builder`

**Classes**:
- `EngineStructureBuilder`

**Functions**:
- `create_unity_structure()`
- `create_unreal_structure()`
- `create_godot_structure()`
- `create_web_structure()`
- `create_blender_structure()`
- `create_all_structures()`

---

### `vaultmind_forge.forge_converter.formats.__init__`

**Exports** (`__all__`):
- `FormatRegistry`
- `AssetPaths`
- `create_registry_with_handlers`
- `FormatType`
- `CompressionQuality`
- `ShaderModel`
- `USDLayerType`
- `FormatHandler`
- `ModelFormatHandler`
- `TextureFormatHandler`
- `AnimationFormatHandler`
- `FBXHandler`
- `DDSHandler`
- `MaterialXHandler`
- `USDHandler`
- `ConversionOptions`
- `RepairOptions`
- `TextureOptions`
- `AnimationOptions`
- `USDExportOptions`
- `ModelMetadata`
- `TextureMetadata`
- `AnimationMetadata`
- `MaterialParameters`
- `AssetError`
- `FormatError`
- `ConversionError`
- `RepairError`

**Functions**:
- `create_registry_with_handlers()`

---

### `vaultmind_forge.forge_converter.formats.dds_handler`

**Classes**:
- `DDSHandler`

**Functions**:
- `get_name()`
- `get_extensions()`
- `can_read()`
- `can_write()`
- `get_description()`
- `detect_format()`
- `convert_to()`
- `compress()`
- `resize()`
- `get_metadata()`

---

### `vaultmind_forge.forge_converter.formats.fbx_handler`

**Classes**:
- `FBXHandler`

**Functions**:
- `get_name()`
- `get_extensions()`
- `can_read()`
- `can_write()`
- `get_description()`
- `detect_format()`
- `convert_to()`
- `optimize()`
- `repair()`
- `get_metadata()`

---

### `vaultmind_forge.forge_converter.formats.format_registry`

**Classes**:
- `AssetPaths`
- `FormatType`
- `CompressionQuality`
- `ConversionOptions`
- `RepairOptions`
- `TextureOptions`
- `AnimationOptions`
- `ModelMetadata`
- `TextureMetadata`
- `AnimationMetadata`
- `AssetError`
- `FormatError`
- `ConversionError`
- `RepairError`
- `FormatHandler`
- `ModelFormatHandler`
- `TextureFormatHandler`
- `AnimationFormatHandler`
- `FormatRegistry`

**Functions**:
- `ensure_all_exist()`
- `to_dict()`
- `to_dict()`
- `to_dict()`
- `get_name()`
- `get_extensions()`
- `can_read()`
- `can_write()`
- `get_description()`
- `detect_format()`
- `convert_to()`
- `optimize()`
- `repair()`
- `get_metadata()`
- `convert_to()`
- `compress()`
- `resize()`
- `get_metadata()`
- `convert_to()`
- `extract_from_model()`
- `get_metadata()`
- `register_model_format()`
- `register_texture_format()`
- `register_animation_format()`
- `get_model_format()`
- `get_texture_format()`
- `get_animation_format()`
- `get_all_handlers()`
- `detect_format()`
- `compute_checksum()`
- `save_metadata()`
- `list_supported_formats()`

---

### `vaultmind_forge.forge_converter.formats.materialx_handler`

**Classes**:
- `ShaderModel`
- `MaterialParameters`
- `MaterialXHandler`

**Functions**:
- `to_dict()`
- `load_material()`
- `save_material()`
- `translate_shader()`
- `export_to_unity()`
- `export_to_unreal()`

---

### `vaultmind_forge.forge_converter.formats.usd_handler`

**Classes**:
- `USDLayerType`
- `USDExportOptions`
- `USDHandler`

**Functions**:
- `get_name()`
- `get_extensions()`
- `can_read()`
- `can_write()`
- `get_description()`
- `detect_format()`
- `convert_to()`
- `optimize()`
- `repair()`
- `get_metadata()`
- `create_layered_stage()`
- `create_variant_set()`

---

### `vaultmind_forge.forge_converter.optimization.__init__`

**Exports** (`__all__`):
- `CoordinateSystem`
- `Vertex`
- `QuadricError`
- `LODCalculator`
- `MeshDecimator`
- `TextureOptimizer`
- `CoordinateTransformer`
- `UVOptimizer`
- `COMPRESSION_BPP`

---

### `vaultmind_forge.forge_converter.optimization.math_utils`

**Classes**:
- `CoordinateSystem`
- `Vertex`
- `QuadricError`
- `LODCalculator`
- `MeshDecimator`
- `TextureOptimizer`
- `CoordinateTransformer`
- `UVOptimizer`

**Functions**:
- `from_triangle()`
- `compute_error()`
- `optimal_position()`
- `screen_coverage_to_distance()`
- `distance_to_screen_coverage()`
- `calculate_lod_distances()`
- `calculate_target_poly_count()`
- `calculate_reduction_percentage()`
- `calculate_mipmap_sizes()`
- `calculate_memory_usage()`
- `compression_ratio()`
- `next_power_of_two()`
- `resize_to_power_of_two()`
- `transform_vertex()`
- `calculate_uv_area()`
- `detect_uv_overlap()`

---

## forge_diffusion

### `vaultmind_forge.forge_diffusion`

**Exports** (`__all__`):
- `DiffusionGenerator`
- `GenerationBackend`
- `GenerationConfig`
- `GenerationResult`
- `HelperPassType`
- `DiffusionGeneratorError`
- `ModelNotLoadedError`
- `InvalidConfigurationError`
- `GenerationFailedError`
- `AgentIntegratedPipeline`
- `AgentPipelineConfig`
- `AgentPipelineResult`
- `create_quick_pipeline`
- `SDXLGenerator`

---

### `vaultmind_forge.forge_diffusion.agent_pipeline`

**Classes**:
- `AgentPipelineConfig`
- `AgentPipelineResult`
- `AgentIntegratedPipeline`

**Functions**:
- `create_quick_pipeline()`
- `initialize()`
- `generate()`
- `generate_batch()`
- `shutdown()`

---

### `vaultmind_forge.forge_diffusion.controlnet`

**Classes**:
- `ControlNetWrapper`

**Functions**:
- `generate_with_controlnet()`
- `load_controlnet()`
- `create_pipeline()`
- `generate()`
- `unload()`

---

### `vaultmind_forge.forge_diffusion.controlnet_preprocessors`

**Functions**:
- `canny_edge_detection()`
- `depth_estimation()`
- `pose_detection()`
- `scribble_detection()`
- `normal_map_estimation()`
- `preprocess_image()`

---

### `vaultmind_forge.forge_diffusion.generator`

**Classes**:
- `GenerationBackend`
- `HelperPassType`
- `GenerationConfig`
- `GenerationResult`
- `DiffusionGeneratorError`
- `ModelNotLoadedError`
- `InvalidConfigurationError`
- `GenerationFailedError`
- `DiffusionGenerator`

**Functions**:
- `load_models()`
- `generate()`
- `generate_multi_pass()`
- `unload_models()`

---

### `vaultmind_forge.forge_diffusion.huggingface_generator`

**Classes**:
- `HuggingFaceDiffusionGenerator`

**Functions**:
- `initialize()`
- `generate()`
- `is_available()`
- `unload_models()`

---

### `vaultmind_forge.forge_diffusion.pixelwave_generator`

**Classes**:
- `PixelWaveGenerator`

**Functions**:
- `initialize()`
- `generate()`
- `apply_style_preset()`
- `get_recommended_resolution()`
- `is_available()`
- `unload_models()`
- `get_stats()`

---

### `vaultmind_forge.forge_diffusion.sdxl_generator`

**Classes**:
- `SDXLGenerator`

**Functions**:
- `initialize()`
- `generate()`
- `is_available()`
- `unload_models()`
- `get_stats()`

---

### `vaultmind_forge.forge_diffusion.waifu_generator`

**Classes**:
- `WaifuGenerator`

**Functions**:
- `initialize()`
- `generate()`
- `generate_variations()`
- `apply_character_type()`
- `get_recommended_resolution()`
- `is_available()`
- `unload_models()`
- `get_stats()`

---

## forge_executor

### `vaultmind_forge.forge_executor`

**Exports** (`__all__`):
- `DAG`
- `Task`
- `Executor`

---

### `vaultmind_forge.forge_executor.executor`

**Classes**:
- `Task`
- `DAG`
- `Executor`

**Functions**:
- `add()`
- `topo_sort()`
- `visit()`

---

### `vaultmind_forge.forge_executor.pipeline`

**Classes**:
- `Task`
- `DAG`
- `Executor`
- `PipelineStage`
- `PipelineResult`
- `AssetPipeline`

**Functions**:
- `run_asset_pipeline()`
- `add_task()`
- `execute()`
- `get_path()`
- `run_generation_pipeline()`
- `visit()`
- `create_dirs()`

---

## forge_intake

### `vaultmind_forge.forge_intake`

**Exports** (`__all__`):
- `IntakeStage`
- `QualityLevel`
- `AssetCategory`
- `get_supported_stages`
- `get_supported_quality_levels`
- `get_supported_categories`

**Classes**:
- `IntakeStage`
- `QualityLevel`
- `AssetCategory`

**Functions**:
- `get_supported_stages()`
- `get_supported_quality_levels()`
- `get_supported_categories()`

---

### `vaultmind_forge.forge_intake.batch_ingest`

**Classes**:
- `AssetMetadata`
- `AssetIngestor`

**Functions**:
- `main()`
- `compute_hash()`
- `detect_category()`
- `analyze_archive_contents()`
- `extract_archive()`
- `analyze_model_characteristics()`
- `generate_vaf_catalog()`
- `generate_tags()`
- `process_asset()`
- `scan_downloads()`
- `batch_process()`

---

### `vaultmind_forge.forge_intake.batch_ingest_v2`

**Classes**:
- `AssetIngestorV2`

**Functions**:
- `main()`
- `compute_hash()`
- `extract_archives()`
- `batch_process()`

---

### `vaultmind_forge.forge_intake.drop_folder_monitor`

**Classes**:
- `AssetDropHandler`
- `DropFolderMonitor`

**Functions**:
- `main()`
- `on_created()`
- `on_modified()`
- `stop()`
- `start()`
- `stop()`
- `run_interactive()`

---

### `vaultmind_forge.forge_intake.forge_daemon`

**Classes**:
- `ForgeDaemon`

**Functions**:
- `start_daemon()`
- `stop_daemon()`
- `status_daemon()`
- `main()`
- `start()`
- `stop()`
- `get_status()`

---

### `vaultmind_forge.forge_intake.format_registry`

**Classes**:
- `FormatFamily`
- `FormatSpec`
- `FormatRegistry`

**Functions**:
- `print_registry_summary()`
- `get_spec()`
- `is_supported()`
- `get_by_family()`
- `get_geometry_formats()`
- `get_texture_formats()`
- `get_archive_formats()`
- `select_best_format()`
- `get_conversion_path()`

---

### `vaultmind_forge.forge_intake.multi_version_handler`

**Classes**:
- `AssetVariant`
- `MultiVersionHandler`

**Functions**:
- `process_with_multi_version()`
- `normalize_asset_name()`
- `group_asset_variants()`
- `select_primary_variant()`
- `merge_variants()`

---

### `vaultmind_forge.forge_intake.unified_converter`

**Classes**:
- `ConversionStatus`
- `ConversionResult`
- `IntermediateRepresentation`
- `UnifiedConverter`

**Functions**:
- `convert_file()`
- `batch_convert()`
- `to_vaf_full()`
- `convert()`

---

## forge_lineage

### `vaultmind_forge.forge_lineage`

**Exports** (`__all__`):
- `LineageTracker`
- `LineageRecord`
- `OperationType`

---

### `vaultmind_forge.forge_lineage.lineage_tracker`

**Classes**:
- `OperationType`
- `LineageRecord`
- `LineageTracker`

**Functions**:
- `to_dict()`
- `compute_checksum()`
- `record_generation()`
- `record_validation()`
- `record_conversion()`
- `record_optimization()`
- `record_retry()`
- `get_asset_history()`
- `get_children()`
- `get_asset_tree()`
- `export_genealogy()`
- `get_statistics()`

---

### `vaultmind_forge.forge_lineage.logger`

**Classes**:
- `LineageLogger`

**Functions**:
- `write_report()`
- `write_diagnostics()`
- `finalize()`

---

## forge_loader

### `vaultmind_forge.forge_loader`

**Classes**:
- `BackendType`
- `BackendStatus`
- `BackendInfo`
- `NativeBackendLoader`
- `BackendRegistry`

**Functions**:
- `load_validator()`
- `get_loader()`
- `load_rust_validator()`
- `load_cpp_validator()`
- `get_backend()`
- `list_backends()`
- `discover_backends()`
- `auto_load_all()`
- `load_with_fallback()`
- `initialize()`
- `get_loader()`
- `load_validator()`
- `get_backend()`

---

## forge_monitor

### `vaultmind_forge.forge_monitor`

**Exports** (`__all__`):
- `SystemMonitor`
- `SystemSnapshot`
- `Alert`
- `AlertLevel`
- `MetricsAggregator`
- `MetricStats`

---

### `vaultmind_forge.forge_monitor.metrics`

**Classes**:
- `MetricStats`
- `MetricsAggregator`

**Functions**:
- `to_dict()`
- `compute_stats()`
- `detect_anomalies()`
- `detect_trend()`
- `time_window_stats()`
- `generate_performance_report()`
- `export_csv()`

---

### `vaultmind_forge.forge_monitor.monitor`

**Classes**:
- `AlertLevel`
- `SystemSnapshot`
- `Alert`
- `SystemMonitor`
- `SessionTracker`

**Functions**:
- `to_dict()`
- `capture_snapshot()`
- `start_session()`
- `stop_session()`
- `track_session()`
- `get_session_summary()`
- `get_current_status()`
- `export_metrics()`

---

## forge_monitor_tui

### `vaultmind_forge.forge_monitor_tui`

**Classes**:
- `ForgeMonitorTUI`

**Functions**:
- `run_monitor()`
- `get_system_stats()`
- `get_active_workflows()`
- `get_recent_outputs()`
- `get_system_info()`
- `get_workflow_tree()`
- `create_layout()`
- `render()`
- `run()`

---

## forge_nodes

### `vaultmind_forge.forge_nodes`

**Exports** (`__all__`):
- `BaseNode`
- `NodeInput`
- `NodeOutput`
- `NodeConnection`
- `NodeCategory`
- `DataType`
- `NodeGraph`
- `GraphExecutor`
- `ExecutionResult`
- `NodeRegistry`
- `register_node`
- `get_node_class`
- `list_nodes`
- `WorkflowTemplate`
- `TemplateManager`
- `load_template`
- `save_template`

---

### `vaultmind_forge.forge_nodes.base_node`

**Classes**:
- `DataType`
- `NodeCategory`
- `NodeInput`
- `NodeOutput`
- `NodeConnection`
- `NodeMetadata`
- `BaseNode`

**Functions**:
- `validate()`
- `execute()`
- `validate_inputs()`
- `get_ai_suggestion()`
- `enable_ai_mode()`
- `disable_ai_mode()`
- `get_help()`
- `to_dict()`
- `from_dict()`

---

### `vaultmind_forge.forge_nodes.nodes.sdxl_node`

**Classes**:
- `SDXLGeneratorNode`

**Functions**:
- `execute()`

---

### `vaultmind_forge.forge_nodes.workflow_template`

**Classes**:
- `WorkflowTemplate`
- `TemplateManager`

**Functions**:
- `load_template()`
- `save_template()`
- `to_dict()`
- `from_dict()`
- `save()`
- `load()`
- `get_template()`
- `list_templates()`
- `create_builtin_templates()`

---

## forge_packaging

### `vaultmind_forge.forge_packaging`

**Exports** (`__all__`):
- `AssetPackager`
- `AssetManifest`
- `PackageInfo`
- `PackagerError`
- `InvalidAssetError`
- `PackagingFailedError`
- `quick_package`

---

### `vaultmind_forge.forge_packaging.packager`

**Classes**:
- `AssetManifest`
- `PackageInfo`
- `PackagerError`
- `InvalidAssetError`
- `PackagingFailedError`
- `AssetPackager`

**Functions**:
- `quick_package()`
- `package_assets()`
- `create_manifest()`
- `extract_package()`
- `get_package_info()`

---

## forge_procedural

### `vaultmind_forge.forge_procedural`

**Exports** (`__all__`):
- `ProceduralGenerator`
- `NoiseType`
- `NoisePreset`
- `OutputStructure`
- `get_output_structure`
- `ensure_output_directories`
- `BillboardGenerator`
- `BillboardType`
- `MaterialType`
- `WeatheringLevel`
- `BillboardConfig`
- `BILLBOARD_PRESETS`

---

### `vaultmind_forge.forge_procedural.billboard_generator`

**Classes**:
- `BillboardType`
- `MaterialType`
- `WeatheringLevel`
- `BillboardConfig`
- `BillboardGenerator`

**Functions**:
- `generate_billboard()`
- `generate_billboard_variations()`
- `save_billboard_complete()`

---

### `vaultmind_forge.forge_procedural.generator`

**Classes**:
- `ProceduralGenerator`

**Functions**:
- `generate_texture()`
- `generate_terrain()`
- `generate_variations()`
- `list_presets()`
- `save_texture_auto()`
- `save_texture()`
- `save_heightmap_auto()`
- `save_heightmap()`

---

### `vaultmind_forge.forge_procedural.noise_types`

**Classes**:
- `NoiseType`
- `NoisePreset`

**Functions**:
- `get_preset()`
- `list_presets()`

---

### `vaultmind_forge.forge_procedural.output_structure`

**Classes**:
- `OutputStructure`

**Functions**:
- `get_output_structure()`
- `ensure_output_directories()`
- `ensure_all_directories()`
- `get_path()`
- `list_categories()`
- `get_all_paths()`
- `create_recursive()`
- `flatten()`

---

## forge_semantic

### `vaultmind_forge.forge_semantic`

**Exports** (`__all__`):
- `SemanticDownrezzer`
- `DownrezResult`
- `DownrezMode`
- `SemanticRegion`
- `downrez_batch`

---

### `vaultmind_forge.forge_semantic.downrez`

**Classes**:
- `DownrezMode`
- `SemanticRegion`
- `DownrezResult`
- `SemanticDownrezzer`

**Functions**:
- `downrez_batch()`
- `to_dict()`
- `downrez()`
- `create_downrez_ladder()`

---

## forge_sr

### `vaultmind_forge.forge_sr`

**Exports** (`__all__`):
- `SuperResolutionUpscaler`
- `SRResult`
- `DualSRComparison`
- `SRBackend`
- `SRQuality`
- `upscale_batch`

---

### `vaultmind_forge.forge_sr.upscaler`

**Classes**:
- `SRBackend`
- `SRQuality`
- `SRResult`
- `DualSRComparison`
- `SuperResolutionUpscaler`

**Functions**:
- `upscale_batch()`
- `to_dict()`
- `to_dict()`
- `upscale()`
- `upscale_dual()`

---

## forge_validator

### `vaultmind_forge.forge_validator`

**Exports** (`__all__`):
- `Validator`
- `ValidationResult`
- `AIValidator`
- `AIValidationResult`
- `ValidationDecision`
- `validate_asset_ai`

---

### `vaultmind_forge.forge_validator.ai_validator`

**Classes**:
- `ValidationDecision`
- `AIValidationResult`
- `AIValidator`

**Functions**:
- `validate_asset_ai()`
- `validate_with_ai()`
- `validate_batch_with_ai()`
- `record_human_feedback()`
- `get_performance_stats()`
- `export_decision_history()`
- `adapt_thresholds()`
- `anatomy_score()`
- `prompt_alignment_score()`
- `consistency_score()`

---

### `vaultmind_forge.forge_validator.backends`

**Classes**:
- `BackendNotAvailable`
- `RustBackend`
- `CppBackend`
- `PythonFallbackBackend`

**Functions**:
- `get_backend()`
- `get_validator()`
- `sharpness_score()`
- `color_histogram()`
- `color_fidelity_score()`
- `validate()`
- `validate()`
- `validate()`

---

### `vaultmind_forge.forge_validator.evaluators`

**Classes**:
- `MetricThresholds`
- `Evaluation`
- `Evaluator`
- `ThreePassRunner`

**Functions**:
- `evaluate()`
- `run()`
- `below()`

---

### `vaultmind_forge.forge_validator.metrics`

**Classes**:
- `Diagnostic`

**Functions**:
- `anatomy_score()`
- `prompt_alignment_score()`
- `consistency_score()`
- `compute_metrics()`

---

### `vaultmind_forge.forge_validator.metrics_advanced`

**Classes**:
- `AnatomyMetrics`
- `PromptAlignmentMetrics`
- `ConsistencyMetrics`

**Functions**:
- `anatomy_score_advanced()`
- `prompt_alignment_score_advanced()`
- `consistency_score_advanced()`
- `dhash()`
- `compute_gram_matrix()`

---

### `vaultmind_forge.forge_validator.validator`

**Classes**:
- `ValidationResult`
- `Validator`

**Functions**:
- `validate_asset()`
- `validate_batch()`
- `get_summary()`

---

## forge_versioning

### `vaultmind_forge.forge_versioning`

**Exports** (`__all__`):
- `AssetVersionControl`
- `AssetVersion`
- `Branch`
- `AssetStatus`

---

### `vaultmind_forge.forge_versioning.version_control`

**Classes**:
- `AssetStatus`
- `AssetVersion`
- `Branch`
- `AssetVersionControl`

**Functions**:
- `to_dict()`
- `from_dict()`
- `to_dict()`
- `from_dict()`
- `commit()`
- `get_history()`
- `checkout()`
- `create_branch()`
- `list_branches()`
- `get_version()`
- `restore_version()`
- `get_current_branch()`
- `compare_branches()`

---

## forge_video

### `vaultmind_forge.forge_video`

**Exports** (`__all__`):
- `VideoGenerator`
- `VideoConfig`
- `VideoResult`
- `TransitionType`
- `VideoCodec`
- `create_slideshow`

---

### `vaultmind_forge.forge_video.generator`

**Classes**:
- `TransitionType`
- `VideoCodec`
- `VideoConfig`
- `VideoResult`
- `VideoGenerator`

**Functions**:
- `sanitize_media_path()`
- `create_slideshow()`
- `to_dict()`
- `to_dict()`
- `frames_to_video()`
- `extract_frames()`
- `concatenate_videos()`

---

## logging_system

### `vaultmind_forge.logging_system`

**Exports** (`__all__`):
- `setup_logging`
- `get_logger`
- `get_error_summary`
- `save_error_log`
- `configure_root_logger`
- `LogEntry`
- `StructuredFormatter`
- `ColoredConsoleFormatter`

**Classes**:
- `LogEntry`
- `StructuredFormatter`
- `ColoredConsoleFormatter`
- `ErrorAggregator`
- `AggregatingHandler`

**Functions**:
- `setup_logging()`
- `get_logger()`
- `get_error_summary()`
- `save_error_log()`
- `configure_root_logger()`
- `to_dict()`
- `to_json()`
- `format()`
- `format()`
- `add_error()`
- `get_summary()`
- `save_to_file()`
- `emit()`

---

## tests

### `vaultmind_forge.tests.test_batch_processing`

**Functions**:
- `test_1_job_queue()`
- `test_2_priority_ordering()`
- `test_3_dependencies()`
- `test_4_resource_manager()`
- `test_5_batch_processor()`
- `test_6_persistence()`
- `run_all_tests()`
- `on_progress()`

---

### `vaultmind_forge.tests.test_billboard_generator`

**Functions**:
- `test_billboard_initialization()`
- `test_generate_industrial_billboard()`
- `test_generate_all_billboard_types()`
- `test_material_variations()`
- `test_weathering_levels()`
- `test_billboard_variations()`
- `test_save_billboard()`
- `test_billboard_presets()`
- `test_output_structure_integration()`
- `run_all_tests()`

---

### `vaultmind_forge.tests.test_cli_checkpoint_manager`

**Classes**:
- `TestCheckpointTypeEnum`
- `TestRecoveryStrategyEnum`
- `TestCheckpointMetadata`
- `TestCheckpointManagerInitialization`
- `TestCheckpointCreation`
- `TestCheckpointListing`
- `TestCheckpointRestoration`
- `TestCheckpointDeletion`
- `TestCheckpointPersistence`
- `TestCheckpointSerialization`

**Functions**:
- `temp_checkpoint_dir()`
- `checkpoint_manager()`
- `workflow_engine()`
- `sample_workflow()`
- `test_checkpoint_type_values()`
- `test_recovery_strategy_values()`
- `test_create_metadata()`
- `test_metadata_to_dict()`
- `test_metadata_from_dict()`
- `test_metadata_with_tags()`
- `test_create_checkpoint_manager()`
- `test_create_checkpoint_manager_custom_settings()`
- `test_checkpoint_directory_created()`
- `test_serialize_workflow()`
- `test_serialize_task()`

---

### `vaultmind_forge.tests.test_cli_distributed_executor`

**Classes**:
- `TestWorkerStatusEnum`
- `TestWorkerTypeEnum`
- `TestLoadBalancingStrategyEnum`
- `TestWorkerMetrics`
- `TestWorker`
- `TestExecutorInitialization`
- `TestTaskSubmission`
- `TestLoadBalancing`
- `TestTaskExecution`
- `TestTaskQueueItem`
- `TestVisualization`

**Functions**:
- `executor()`
- `sample_worker()`
- `sample_task()`
- `test_worker_status_values()`
- `test_worker_type_values()`
- `test_load_balancing_strategy_values()`
- `test_initial_metrics()`
- `test_update_task_completion_success()`
- `test_update_task_completion_failure()`
- `test_update_multiple_tasks()`
- `test_success_rate()`
- `test_success_rate_no_tasks()`
- `test_efficiency_score()`
- `test_create_worker()`
- `test_worker_with_gpu()`
- `test_can_handle_task_general()`
- `test_can_handle_task_gpu_required()`
- `test_can_handle_task_gpu_worker()`
- `test_can_handle_task_gpu_worker_rejects_cpu_task()`
- `test_can_handle_task_agent_required()`
- `test_can_handle_task_wrong_status()`
- `test_load_score_idle()`
- `test_load_score_with_current_task()`
- `test_load_score_with_queue()`
- `test_load_score_high_resource_usage()`
- `test_create_executor_default()`
- `test_create_executor_custom_workers()`
- `test_create_executor_custom_strategy()`
- `test_detect_system_capabilities()`
- `test_design_worker_pool_cpu_only()`
- `test_design_worker_pool_with_gpu()`
- `test_round_robin_select()`
- `test_least_loaded_select()`
- `test_resource_aware_select_gpu_task()`
- `test_resource_aware_select_considers_efficiency()`
- `test_adaptive_select()`
- `test_create_queue_item()`
- `test_queue_item_with_custom_attempts()`

---

### `vaultmind_forge.tests.test_cli_multi_modal_pipeline`

**Classes**:
- `TestModalityEnums`
- `TestModalSpec`
- `TestEnhancementRules`
- `TestQualityThresholds`
- `TestPipelineCreation`
- `TestTopologicalSort`
- `TestParallelGroups`
- `TestExecutionPlan`
- `TestPipelineExecution`
- `TestQualityCalculation`
- `TestCrossModalConsistency`
- `TestEnhancementContext`
- `TestVisualization`

**Functions**:
- `agent_manager()`
- `process_orchestrator()`
- `workflow_engine()`
- `pipeline()`
- `test_modality_values()`
- `test_modal_quality_values()`
- `test_create_basic_modal_spec()`
- `test_modal_spec_with_dependencies()`
- `test_modal_spec_with_custom_params()`
- `test_enhancement_rules_structure()`
- `test_image_enhanced_by_text()`
- `test_image_enhanced_by_audio()`
- `test_cross_modal_enhancement_bidirectional()`
- `test_quality_thresholds()`
- `test_quality_threshold_ordering()`
- `test_topological_sort_no_dependencies()`
- `test_topological_sort_with_dependencies()`
- `test_topological_sort_circular_dependency()`
- `test_parallel_groups_no_dependencies()`
- `test_parallel_groups_with_dependencies()`
- `test_execution_plan_structure()`
- `test_execution_plan_critical_path()`
- `test_execution_plan_parallelism_factor()`
- `test_calculate_overall_quality()`
- `test_calculate_overall_quality_empty()`
- `test_identify_refinement_targets()`
- `test_consistency_single_modality()`
- `test_consistency_multiple_modalities()`
- `test_calculate_modal_consistency()`
- `test_build_enhancement_context()`
- `test_build_enhancement_context_missing_source()`
- `test_visualize_pipeline()`
- `test_visualize_nonexistent_pipeline()`

---

### `vaultmind_forge.tests.test_cli_task_decomposer`

**Classes**:
- `TestTaskContextAnalysis`
- `TestPatternMatching`
- `TestWorkflowGeneration`
- `TestFullDecomposition`
- `TestTaskTypeInference`
- `TestConfidenceCalculation`
- `TestDurationEstimation`
- `TestLearningSystem`
- `TestVisualization`

**Functions**:
- `agent_manager()`
- `process_orchestrator()`
- `workflow_engine()`
- `decomposer()`
- `test_match_image_generation()`
- `test_match_character_creation()`
- `test_match_terrain_generation()`
- `test_match_batch_validation()`
- `test_no_pattern_match()`
- `test_infer_generation_type()`
- `test_infer_validation_type()`
- `test_infer_enhancement_type()`
- `test_infer_analysis_type()`
- `test_infer_processing_type()`
- `test_confidence_with_pattern_match()`
- `test_confidence_without_pattern_match()`
- `test_trivial_duration()`
- `test_epic_duration()`
- `test_generation_duration_multiplier()`
- `test_learn_from_execution()`
- `test_multiple_execution_history()`
- `test_visualize_decomposition()`

---

### `vaultmind_forge.tests.test_format_handlers`

**Functions**:
- `setup_test_environment()`
- `create_test_image()`
- `test_1_format_registry()`
- `test_2_dds_handler()`
- `test_3_materialx_handler()`
- `test_4_usd_handler()`
- `test_5_fbx_handler()`
- `run_all_tests()`

---

### `vaultmind_forge.tests.test_integrated_pipeline`

**Functions**:
- `setup_test_environment()`
- `test_1_ai_validator_standalone()`
- `test_2_lineage_tracker_standalone()`
- `test_3_pipeline_dag()`
- `test_4_integrated_workflow()`
- `test_5_retry_logic()`
- `run_all_tests()`

---

### `vaultmind_forge.tests.test_model_manager`

**Classes**:
- `MockModel`

**Functions**:
- `create_mock_loader()`
- `test_model_registration()`
- `test_model_loading()`
- `test_model_unloading()`
- `test_context_manager()`
- `test_memory_eviction()`
- `test_keep_loaded()`
- `test_multiple_loads()`
- `test_get_stats()`
- `test_thread_safety()`
- `test_auto_unload_disabled()`
- `generate()`
- `loader()`
- `worker()`

---

### `vaultmind_forge.tests.test_output_structure`

**Functions**:
- `test_output_structure_creation()`
- `test_category_listing()`
- `test_path_resolution()`
- `test_all_paths_flat()`
- `test_generator_integration()`
- `test_auto_save_paths()`
- `run_all_tests()`

---

### `vaultmind_forge.tests.test_procedural_generation`

**Functions**:
- `test_generator_initialization()`
- `test_texture_presets()`
- `test_terrain_presets()`
- `test_noise_types()`
- `test_variations()`
- `test_parameter_override()`
- `test_seed_reproducibility()`
- `test_list_presets()`
- `test_file_save()`
- `run_all_tests()`

---

### `vaultmind_forge.tests.test_quality_guardian`

**Functions**:
- `create_test_image()`
- `test_1_agent_initialization()`
- `test_2_assess_good_quality()`
- `test_3_auto_fix_blurry()`
- `test_4_auto_fix_contrast()`
- `test_5_auto_fix_brightness()`
- `test_6_metrics_and_reporting()`
- `test_7_escalation_logic()`
- `test_8_agent_status()`
- `run_all_tests()`

---

### `vaultmind_forge.tests.test_style_profiles`

**Classes**:
- `TestStyleProfiles`
- `TestStyleDetection`
- `TestParameterOptimization`
- `TestParameterValidation`
- `TestQualityGuardianIntegration`
- `TestPromptEnhancement`
- `TestCompletePipeline`

**Functions**:
- `run_tests()`
- `test_1_profile_exists()`
- `test_2_profile_has_required_fields()`
- `test_3_parameter_ranges()`
- `test_4_anime_clip_skip()`
- `test_1_detect_anime()`
- `test_2_detect_photorealistic()`
- `test_3_detect_pixel_art()`
- `test_4_explicit_style_tag()`
- `test_1_get_recommended_params()`
- `test_2_params_increase_on_retry()`
- `test_3_user_overrides()`
- `test_4_output_type_adjustment()`
- `test_1_valid_anime_params()`
- `test_2_invalid_anime_clip_skip()`
- `test_3_excessive_cfg()`
- `test_4_out_of_range()`
- `test_1_create_style_aware_guardian()`
- `test_2_different_thresholds_per_style()`
- `test_1_enhance_basic_prompt()`
- `test_2_quality_level_affects_enhancement()`
- `test_3_negative_prompt_generation()`
- `test_1_create_pipeline()`
- `test_2_explicit_style_override()`

---


# Backend (FastAPI)

## backend/api.py

**Purpose**: FastAPI REST API exposing Python modules

**Endpoints**:
- `GET /` - Root/health
- `POST /api/workflows` - Save workflow
- `GET /api/workflows/{id}` - Get workflow
- `GET /api/workflows` - List workflows
- `POST /api/execute` - Execute workflow
- `GET /api/execute/{id}/progress` - Get execution progress
- `GET /api/nodes` - List available nodes
- `GET /api/health` - Health check
- `GET /api/auth/status` - Authentication status
- `GET /api/filesystem/browse` - Browse filesystem
- `GET /api/filesystem/thumbnail` - Get image thumbnail

## backend/auth.py

**Functions**:
- `verify_api_key()` - Verify API key dependency
- `get_auth_status()` - Get auth configuration status

## backend/core/engine.py

**Classes**:
- `NodeExecutionEngine` - Type-safe workflow execution engine
- `ValidationError` - Workflow validation errors
- `ExecutionError` - Workflow execution errors

## backend/core/registry.py

**Functions**:
- `create_default_registry()` - Create executor registry with all nodes

## backend/executors/

Node executors for each forge module (thin wrappers):
- `sdxl_executor.py` - Wraps forge_diffusion.SDXLGenerator
- `validator_executor.py` - Wraps forge_validator
- `upscale_executor.py` - Wraps forge_sr
- etc.

---

# Web UI (React + Vite)

## web_ui/src/App.jsx

**Main application component with node editor**

## web_ui/src/components/

**Node Editor Components**:
- `NodeEditor.jsx` - React Flow canvas
- `CustomNode.jsx` - Base node component
- `ConnectionLine.jsx` - Custom connection lines

**Node Type Components**:
- `SDXLGeneratorNode.jsx` - SDXL generation node
- `ValidatorNode.jsx` - Asset validation node
- `UpscaleNode.jsx` - Super resolution node
- `VideoGeneratorNode.jsx` - Video generation node
- etc.

**UI Components**:
- `Sidebar.jsx` - Node palette
- `ExecuteButton.jsx` - Workflow execution
- `ProgressModal.jsx` - Execution progress
- `PreviewPanel.jsx` - Result previews

---

# Scripts & Tools

## examples/

- `python_first_workflows.py` - 6 Python-only workflow examples
- `test_rust_validators.py` - Rust validator integration test

## Root Scripts

- `create_component_inventory.py` - This inventory generator

---

# Project Structure Summary

```
vaultmind_forge/           # Python core (141 modules)
  ├── forge_diffusion/     # Image generation (SDXL, etc.)
  ├── forge_video/         # Video generation
  ├── forge_sr/            # Super resolution
  ├── forge_semantic/      # Semantic downscaling
  ├── forge_validator/     # Quality validation
  ├── forge_agents/        # 5 AI agents
  ├── forge_bots/          # 4 automation bots
  ├── forge_ai/            # AI backends (12 backends)
  ├── forge_converter/     # Format conversion
  ├── forge_lineage/       # Asset lineage tracking
  ├── forge_monitor/       # System monitoring
  ├── forge_batch/         # Batch processing
  ├── forge_executor/      # Pipeline execution
  ├── forge_procedural/    # Procedural generation
  ├── forge_3d/            # 3D mesh generation
  ├── forge_packaging/     # Asset packaging
  ├── forge_versioning/    # Version control
  ├── forge_intake/        # Asset intake
  ├── forge_nodes/         # Node system
  ├── cli/                 # Advanced CLI features
  ├── native/              # Rust/C++ validators
  │   ├── rust/validator/  # PyO3 Rust validators
  │   └── cpp/validators/  # pybind11 C++ validators
  └── forge_cli.py         # Main CLI entry point

backend/                   # FastAPI API layer
  ├── api.py               # Main API
  ├── auth.py              # Authentication
  ├── core/                # Execution engine
  │   ├── engine.py        # Workflow executor
  │   └── registry.py      # Node registry
  └── executors/           # Node executors (wrappers)

web_ui/                    # React visualization layer
  ├── src/
  │   ├── App.jsx          # Main app
  │   ├── components/      # UI components
  │   │   ├── NodeEditor.jsx
  │   │   ├── CustomNode.jsx
  │   │   └── nodes/       # Node type components
  │   └── utils.js         # Utilities
  └── package.json

docs/                      # Documentation
examples/                  # Usage examples
tests/                     # Test suites
```

---

# Key Classes & Functions Quick Reference

## Image Generation

- `SDXLGenerator` - vaultmind_forge.forge_diffusion.sdxl_generator
- `HuggingFaceDiffusionGenerator` - vaultmind_forge.forge_diffusion.huggingface_generator
- `PixelWaveGenerator` - vaultmind_forge.forge_diffusion.pixelwave_generator
- `WaifuGenerator` - vaultmind_forge.forge_diffusion.waifu_generator
- `GenerationConfig` - vaultmind_forge.forge_diffusion.generator

## Video Generation

- `VideoGenerator` - vaultmind_forge.forge_video.generator
- `frames_to_video()` - vaultmind_forge.forge_video.generator
- `concatenate_videos()` - vaultmind_forge.forge_video.generator

## Enhancement

- `RealESRGANUpscaler` - vaultmind_forge.forge_sr.upscaler
- `SemanticDownrezzer` - vaultmind_forge.forge_semantic.downrez

## Validation

- `compute_metrics()` - vaultmind_forge.forge_validator.metrics
- `sharpness_score()` - vaultmind_forge.forge_validator.backends
- `color_fidelity_score()` - vaultmind_forge.forge_validator.backends

## AI Agents

- `QualityGuardian` - vaultmind_forge.forge_agents.quality_guardian
- `PromptRefiner` - vaultmind_forge.forge_agents.prompt_refiner
- `ParameterOptimizer` - vaultmind_forge.forge_agents.parameter_optimizer
- `MaterialSuggester` - vaultmind_forge.forge_agents.material_suggester
- `ResolutionAdvisor` - vaultmind_forge.forge_agents.resolution_advisor

## Bots

- `MonitorBot` - vaultmind_forge.forge_bots.monitor_bot
- `QABot` - vaultmind_forge.forge_bots.qa_bot
- `OptimizerBot` - vaultmind_forge.forge_bots.optimizer_bot
- `LineageBot` - vaultmind_forge.forge_bots.lineage_bot

## Lineage

- `LineageLogger` - vaultmind_forge.forge_lineage.logger
- `LineageTracker` - vaultmind_forge.forge_lineage.lineage_tracker

## Monitoring

- `SystemMonitor` - vaultmind_forge.forge_monitor.monitor

## Batch Processing

- `BatchProcessor` - vaultmind_forge.forge_batch.batch_processor
- `JobQueue` - vaultmind_forge.forge_batch.job_queue

---

**Total Components**:
- Python Modules: 141
- Top-level Modules: 30
- FastAPI Endpoints: 11
- React Components: 20+
- AI Backends: 12
- AI Agents: 5
- Automation Bots: 4
- Rust Validators: 3
- Example Scripts: 2

**This is the definitive reference**. All classes and functions listed here ACTUALLY EXIST in the codebase.
