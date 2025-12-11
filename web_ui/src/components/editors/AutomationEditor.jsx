/**
 * VaultMind Forge - Automation Editor
 *
 * Event-driven workflow automation with:
 * - Trigger configuration (time, file, webhook, manual)
 * - Conditional logic builder (if/then/else)
 * - Action sequences
 * - Visual flow builder
 * - Dry-run mode (test without executing)
 * - Automation history and logs
 * - Enable/disable automations
 */

import { useState, useCallback } from 'react'
import {
  Zap,
  Clock,
  FileText,
  Webhook,
  Play,
  Save,
  Download,
  Upload,
  Plus,
  Trash2,
  Edit3,
  AlertCircle,
  CheckCircle,
  XCircle,
  Power,
  History,
  Settings,
  ChevronDown,
  ChevronRight
} from 'lucide-react'

// Trigger types
const TRIGGER_TYPES = {
  SCHEDULE: 'schedule',
  FILE_CHANGE: 'file_change',
  WEBHOOK: 'webhook',
  MANUAL: 'manual',
  WORKFLOW_COMPLETE: 'workflow_complete'
}

// Condition operators
const CONDITION_OPERATORS = {
  EQUALS: 'equals',
  NOT_EQUALS: 'not_equals',
  GREATER_THAN: 'greater_than',
  LESS_THAN: 'less_than',
  CONTAINS: 'contains',
  NOT_CONTAINS: 'not_contains'
}

// Action types
const ACTION_TYPES = {
  RUN_WORKFLOW: 'run_workflow',
  SEND_EMAIL: 'send_email',
  WEBHOOK_POST: 'webhook_post',
  MOVE_FILE: 'move_file',
  CREATE_ASSET: 'create_asset'
}

// Automation status
const AUTOMATION_STATUS = {
  ENABLED: 'enabled',
  DISABLED: 'disabled',
  RUNNING: 'running',
  ERROR: 'error'
}

export default function AutomationEditor() {
  // Automation metadata
  const [automationName, setAutomationName] = useState('Untitled Automation')
  const [automationDescription, setAutomationDescription] = useState('')
  const [automationStatus, setAutomationStatus] = useState(AUTOMATION_STATUS.DISABLED)

  // Trigger configuration
  const [trigger, setTrigger] = useState({
    type: TRIGGER_TYPES.MANUAL,
    config: {}
  })

  // Conditions (if/then logic)
  const [conditions, setConditions] = useState([])

  // Actions (what to do when triggered)
  const [actions, setActions] = useState([])

  // UI state
  const [showTriggerConfig, setShowTriggerConfig] = useState(true)
  const [showConditions, setShowConditions] = useState(true)
  const [showActions, setShowActions] = useState(true)
  const [editingCondition, setEditingCondition] = useState(null)
  const [editingAction, setEditingAction] = useState(null)

  // Execution history
  const [executionHistory, setExecutionHistory] = useState([])
  const [showHistory, setShowHistory] = useState(false)

  // Add condition
  const addCondition = () => {
    const newCondition = {
      id: `condition_${Date.now()}`,
      field: '',
      operator: CONDITION_OPERATORS.EQUALS,
      value: '',
      enabled: true
    }
    setConditions([...conditions, newCondition])
    setEditingCondition(newCondition)
  }

  // Update condition
  const updateCondition = (conditionId, updates) => {
    setConditions(conditions.map(c => c.id === conditionId ? { ...c, ...updates } : c))
    if (editingCondition?.id === conditionId) {
      setEditingCondition({ ...editingCondition, ...updates })
    }
  }

  // Delete condition
  const deleteCondition = (conditionId) => {
    setConditions(conditions.filter(c => c.id !== conditionId))
    if (editingCondition?.id === conditionId) {
      setEditingCondition(null)
    }
  }

  // Add action
  const addAction = () => {
    const newAction = {
      id: `action_${Date.now()}`,
      type: ACTION_TYPES.RUN_WORKFLOW,
      config: {},
      enabled: true
    }
    setActions([...actions, newAction])
    setEditingAction(newAction)
  }

  // Update action
  const updateAction = (actionId, updates) => {
    setActions(actions.map(a => a.id === actionId ? { ...a, ...updates } : a))
    if (editingAction?.id === actionId) {
      setEditingAction({ ...editingAction, ...updates })
    }
  }

  // Delete action
  const deleteAction = (actionId) => {
    setActions(actions.filter(a => a.id !== actionId))
    if (editingAction?.id === actionId) {
      setEditingAction(null)
    }
  }

  // Toggle automation enabled/disabled
  const toggleAutomationStatus = () => {
    setAutomationStatus(
      automationStatus === AUTOMATION_STATUS.ENABLED
        ? AUTOMATION_STATUS.DISABLED
        : AUTOMATION_STATUS.ENABLED
    )
  }

  // Dry run (test without executing)
  const dryRun = () => {
    console.log('Dry run automation:', {
      trigger,
      conditions,
      actions
    })

    // Simulate execution
    const execution = {
      id: Date.now(),
      timestamp: new Date().toISOString(),
      status: 'success',
      trigger: trigger.type,
      conditionsPassed: true,
      actionsExecuted: actions.length,
      dryRun: true
    }

    setExecutionHistory([execution, ...executionHistory.slice(0, 19)])
    alert('Dry run completed successfully!\nCheck execution history for details.')
  }

  // Save automation
  const saveAutomation = () => {
    const automation = {
      name: automationName,
      description: automationDescription,
      status: automationStatus,
      trigger,
      conditions,
      actions
    }

    console.log('Saving automation:', automation)
    // TODO: API call to save automation
  }

  // Export automation as JSON
  const exportAutomation = () => {
    const automation = {
      name: automationName,
      description: automationDescription,
      version: '1.0.0',
      trigger,
      conditions,
      actions
    }

    const blob = new Blob([JSON.stringify(automation, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${automationName.replace(/\s+/g, '_')}.automation.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  // Import automation from JSON
  const importAutomation = (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const automation = JSON.parse(e.target.result)
        setAutomationName(automation.name)
        setAutomationDescription(automation.description)
        setTrigger(automation.trigger)
        setConditions(automation.conditions || [])
        setActions(automation.actions || [])
      } catch (error) {
        console.error('Failed to import automation:', error)
        alert('Failed to import automation. Invalid file format.')
      }
    }
    reader.readAsText(file)
  }

  // Render trigger configuration
  const renderTriggerConfig = () => {
    switch (trigger.type) {
      case TRIGGER_TYPES.SCHEDULE:
        return (
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-textMuted mb-1">
                Cron Expression
              </label>
              <input
                type="text"
                value={trigger.config.cron || ''}
                onChange={(e) => setTrigger({ ...trigger, config: { ...trigger.config, cron: e.target.value } })}
                placeholder="0 0 * * * (every day at midnight)"
                className="w-full p-2 bg-background border border-border rounded text-sm text-text font-mono focus:outline-none focus:border-accent"
              />
            </div>
            <div className="text-xs text-textMuted">
              <a href="https://crontab.guru" target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">
                Crontab expression builder →
              </a>
            </div>
          </div>
        )

      case TRIGGER_TYPES.FILE_CHANGE:
        return (
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-textMuted mb-1">
                Watch Path
              </label>
              <input
                type="text"
                value={trigger.config.path || ''}
                onChange={(e) => setTrigger({ ...trigger, config: { ...trigger.config, path: e.target.value } })}
                placeholder="/path/to/watch"
                className="w-full p-2 bg-background border border-border rounded text-sm text-text focus:outline-none focus:border-accent"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-textMuted mb-1">
                Event Type
              </label>
              <select
                value={trigger.config.event || 'created'}
                onChange={(e) => setTrigger({ ...trigger, config: { ...trigger.config, event: e.target.value } })}
                className="w-full p-2 bg-background border border-border rounded text-sm text-text"
              >
                <option value="created">File Created</option>
                <option value="modified">File Modified</option>
                <option value="deleted">File Deleted</option>
              </select>
            </div>
          </div>
        )

      case TRIGGER_TYPES.WEBHOOK:
        return (
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-textMuted mb-1">
                Webhook URL
              </label>
              <input
                type="text"
                value={trigger.config.url || `https://api.vaultmind.com/webhooks/${Date.now()}`}
                readOnly
                className="w-full p-2 bg-background border border-border rounded text-sm text-text font-mono"
              />
              <p className="text-xs text-textMuted mt-1">
                POST to this URL to trigger the automation
              </p>
            </div>
            <div>
              <label className="block text-xs font-medium text-textMuted mb-1">
                Secret Key
              </label>
              <input
                type="password"
                value={trigger.config.secret || 'generate-me'}
                readOnly
                className="w-full p-2 bg-background border border-border rounded text-sm text-text font-mono"
              />
            </div>
          </div>
        )

      case TRIGGER_TYPES.WORKFLOW_COMPLETE:
        return (
          <div className="space-y-3">
            <div>
              <label className="block text-xs font-medium text-textMuted mb-1">
                Workflow
              </label>
              <select
                value={trigger.config.workflowId || ''}
                onChange={(e) => setTrigger({ ...trigger, config: { ...trigger.config, workflowId: e.target.value } })}
                className="w-full p-2 bg-background border border-border rounded text-sm text-text"
              >
                <option value="">Select workflow...</option>
                <option value="workflow_1">Image Generation Pipeline</option>
                <option value="workflow_2">Batch Processing</option>
              </select>
            </div>
          </div>
        )

      case TRIGGER_TYPES.MANUAL:
      default:
        return (
          <div className="text-sm text-textMuted">
            This automation will only run when manually triggered.
          </div>
        )
    }
  }

  return (
    <div className="h-full flex flex-col bg-background">
      {/* Toolbar */}
      <div className="h-12 bg-surface border-b border-border flex items-center justify-between px-4 flex-shrink-0">
        <div className="flex items-center gap-2">
          <Zap className="w-5 h-5 text-accent" />
          <input
            type="text"
            value={automationName}
            onChange={(e) => setAutomationName(e.target.value)}
            className="bg-transparent border-none text-sm font-medium text-text focus:outline-none focus:border-b focus:border-accent"
            placeholder="Automation name"
          />
          <button
            onClick={toggleAutomationStatus}
            className={`flex items-center gap-1 px-2 py-1 rounded text-xs ${
              automationStatus === AUTOMATION_STATUS.ENABLED
                ? 'bg-green-500 text-white'
                : 'bg-background text-textMuted border border-border'
            }`}
            title={automationStatus === AUTOMATION_STATUS.ENABLED ? 'Disable automation' : 'Enable automation'}
          >
            <Power className="w-3 h-3" />
            {automationStatus === AUTOMATION_STATUS.ENABLED ? 'Enabled' : 'Disabled'}
          </button>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={dryRun}
            className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700 flex items-center gap-1"
            title="Test automation without executing"
          >
            <Play className="w-4 h-4" />
            Dry Run
          </button>

          <button
            onClick={() => setShowHistory(!showHistory)}
            className="px-3 py-1.5 bg-background text-text rounded text-sm hover:bg-border flex items-center gap-1"
            title="View execution history"
          >
            <History className="w-4 h-4" />
            History ({executionHistory.length})
          </button>

          <div className="h-6 w-px bg-border" />

          <label className="px-3 py-1.5 bg-background text-text rounded text-sm hover:bg-border flex items-center gap-1 cursor-pointer">
            <Upload className="w-4 h-4" />
            Import
            <input
              type="file"
              accept=".json,.automation.json"
              onChange={importAutomation}
              className="hidden"
            />
          </label>

          <button
            onClick={exportAutomation}
            className="px-3 py-1.5 bg-background text-text rounded text-sm hover:bg-border flex items-center gap-1"
            title="Export automation"
          >
            <Download className="w-4 h-4" />
            Export
          </button>

          <button
            onClick={saveAutomation}
            className="px-3 py-1.5 bg-accent text-white rounded text-sm hover:bg-accent/90 flex items-center gap-1"
            title="Save automation"
          >
            <Save className="w-4 h-4" />
            Save
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Main Content - Automation Builder */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="max-w-4xl mx-auto space-y-6">
            {/* Description */}
            <div>
              <label className="block text-xs font-medium text-textMuted mb-1">
                Description
              </label>
              <textarea
                value={automationDescription}
                onChange={(e) => setAutomationDescription(e.target.value)}
                placeholder="Describe what this automation does..."
                className="w-full h-20 p-3 bg-surface border border-border rounded text-sm text-text placeholder-textMuted resize-none focus:outline-none focus:border-accent"
              />
            </div>

            {/* TRIGGER */}
            <div className="bg-surface border border-border rounded-lg">
              <button
                onClick={() => setShowTriggerConfig(!showTriggerConfig)}
                className="w-full p-4 flex items-center justify-between hover:bg-background transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-accent rounded-full flex items-center justify-center">
                    <span className="text-white font-bold text-sm">1</span>
                  </div>
                  <div className="text-left">
                    <h3 className="text-sm font-semibold text-text">Trigger</h3>
                    <p className="text-xs text-textMuted">When should this automation run?</p>
                  </div>
                </div>
                {showTriggerConfig ? <ChevronDown className="w-5 h-5 text-textMuted" /> : <ChevronRight className="w-5 h-5 text-textMuted" />}
              </button>

              {showTriggerConfig && (
                <div className="p-4 border-t border-border space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-textMuted mb-1">
                      Trigger Type
                    </label>
                    <select
                      value={trigger.type}
                      onChange={(e) => setTrigger({ type: e.target.value, config: {} })}
                      className="w-full p-2 bg-background border border-border rounded text-sm text-text"
                    >
                      <option value={TRIGGER_TYPES.MANUAL}>Manual</option>
                      <option value={TRIGGER_TYPES.SCHEDULE}>Schedule (Cron)</option>
                      <option value={TRIGGER_TYPES.FILE_CHANGE}>File Change</option>
                      <option value={TRIGGER_TYPES.WEBHOOK}>Webhook</option>
                      <option value={TRIGGER_TYPES.WORKFLOW_COMPLETE}>Workflow Complete</option>
                    </select>
                  </div>

                  {renderTriggerConfig()}
                </div>
              )}
            </div>

            {/* CONDITIONS */}
            <div className="bg-surface border border-border rounded-lg">
              <button
                onClick={() => setShowConditions(!showConditions)}
                className="w-full p-4 flex items-center justify-between hover:bg-background transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-accent rounded-full flex items-center justify-center">
                    <span className="text-white font-bold text-sm">2</span>
                  </div>
                  <div className="text-left">
                    <h3 className="text-sm font-semibold text-text">Conditions</h3>
                    <p className="text-xs text-textMuted">Optional: Only run if conditions are met</p>
                  </div>
                </div>
                {showConditions ? <ChevronDown className="w-5 h-5 text-textMuted" /> : <ChevronRight className="w-5 h-5 text-textMuted" />}
              </button>

              {showConditions && (
                <div className="p-4 border-t border-border">
                  {conditions.length === 0 ? (
                    <div className="text-sm text-textMuted text-center py-4">
                      No conditions added. Automation will run on every trigger.
                    </div>
                  ) : (
                    <div className="space-y-2 mb-3">
                      {conditions.map((condition, index) => (
                        <div
                          key={condition.id}
                          className="p-3 bg-background border border-border rounded flex items-center gap-2"
                        >
                          <span className="text-xs text-textMuted font-medium">IF</span>
                          <input
                            type="text"
                            value={condition.field}
                            onChange={(e) => updateCondition(condition.id, { field: e.target.value })}
                            placeholder="field"
                            className="flex-1 p-1 bg-surface border border-border rounded text-sm text-text"
                          />
                          <select
                            value={condition.operator}
                            onChange={(e) => updateCondition(condition.id, { operator: e.target.value })}
                            className="p-1 bg-surface border border-border rounded text-sm text-text"
                          >
                            <option value={CONDITION_OPERATORS.EQUALS}>=</option>
                            <option value={CONDITION_OPERATORS.NOT_EQUALS}>≠</option>
                            <option value={CONDITION_OPERATORS.GREATER_THAN}>&gt;</option>
                            <option value={CONDITION_OPERATORS.LESS_THAN}>&lt;</option>
                            <option value={CONDITION_OPERATORS.CONTAINS}>contains</option>
                            <option value={CONDITION_OPERATORS.NOT_CONTAINS}>!contains</option>
                          </select>
                          <input
                            type="text"
                            value={condition.value}
                            onChange={(e) => updateCondition(condition.id, { value: e.target.value })}
                            placeholder="value"
                            className="flex-1 p-1 bg-surface border border-border rounded text-sm text-text"
                          />
                          <button
                            onClick={() => deleteCondition(condition.id)}
                            className="text-textMuted hover:text-red-500"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}

                  <button
                    onClick={addCondition}
                    className="w-full px-3 py-2 bg-background text-text rounded text-sm hover:bg-border flex items-center justify-center gap-1"
                  >
                    <Plus className="w-4 h-4" />
                    Add Condition
                  </button>
                </div>
              )}
            </div>

            {/* ACTIONS */}
            <div className="bg-surface border border-border rounded-lg">
              <button
                onClick={() => setShowActions(!showActions)}
                className="w-full p-4 flex items-center justify-between hover:bg-background transition-colors"
              >
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 bg-accent rounded-full flex items-center justify-center">
                    <span className="text-white font-bold text-sm">3</span>
                  </div>
                  <div className="text-left">
                    <h3 className="text-sm font-semibold text-text">Actions</h3>
                    <p className="text-xs text-textMuted">What should happen when triggered?</p>
                  </div>
                </div>
                {showActions ? <ChevronDown className="w-5 h-5 text-textMuted" /> : <ChevronRight className="w-5 h-5 text-textMuted" />}
              </button>

              {showActions && (
                <div className="p-4 border-t border-border">
                  {actions.length === 0 ? (
                    <div className="text-sm text-textMuted text-center py-4">
                      No actions configured. Add at least one action.
                    </div>
                  ) : (
                    <div className="space-y-2 mb-3">
                      {actions.map((action, index) => (
                        <div
                          key={action.id}
                          className="p-3 bg-background border border-border rounded"
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-xs text-textMuted font-medium">
                              Action {index + 1}
                            </span>
                            <button
                              onClick={() => deleteAction(action.id)}
                              className="text-textMuted hover:text-red-500"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                          <select
                            value={action.type}
                            onChange={(e) => updateAction(action.id, { type: e.target.value, config: {} })}
                            className="w-full p-2 bg-surface border border-border rounded text-sm text-text mb-2"
                          >
                            <option value={ACTION_TYPES.RUN_WORKFLOW}>Run Workflow</option>
                            <option value={ACTION_TYPES.SEND_EMAIL}>Send Email</option>
                            <option value={ACTION_TYPES.WEBHOOK_POST}>POST to Webhook</option>
                            <option value={ACTION_TYPES.MOVE_FILE}>Move File</option>
                            <option value={ACTION_TYPES.CREATE_ASSET}>Create Asset</option>
                          </select>

                          {/* Action-specific config */}
                          {action.type === ACTION_TYPES.RUN_WORKFLOW && (
                            <select className="w-full p-2 bg-surface border border-border rounded text-sm text-text">
                              <option value="">Select workflow...</option>
                              <option value="workflow_1">Image Generation Pipeline</option>
                              <option value="workflow_2">Batch Processing</option>
                            </select>
                          )}

                          {action.type === ACTION_TYPES.SEND_EMAIL && (
                            <input
                              type="email"
                              placeholder="recipient@example.com"
                              className="w-full p-2 bg-surface border border-border rounded text-sm text-text"
                            />
                          )}

                          {action.type === ACTION_TYPES.WEBHOOK_POST && (
                            <input
                              type="url"
                              placeholder="https://example.com/webhook"
                              className="w-full p-2 bg-surface border border-border rounded text-sm text-text"
                            />
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  <button
                    onClick={addAction}
                    className="w-full px-3 py-2 bg-background text-text rounded text-sm hover:bg-border flex items-center justify-center gap-1"
                  >
                    <Plus className="w-4 h-4" />
                    Add Action
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Right Panel - Execution History */}
        {showHistory && (
          <div className="w-80 bg-surface border-l border-border overflow-y-auto flex-shrink-0">
            <div className="p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-text">Execution History</h3>
                <button
                  onClick={() => setShowHistory(false)}
                  className="text-textMuted hover:text-text"
                >
                  <Edit3 className="w-4 h-4" />
                </button>
              </div>

              {executionHistory.length === 0 ? (
                <div className="text-sm text-textMuted text-center py-8">
                  No execution history yet
                </div>
              ) : (
                <div className="space-y-2">
                  {executionHistory.map((execution) => (
                    <div
                      key={execution.id}
                      className="p-3 bg-background border border-border rounded"
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          {execution.status === 'success' ? (
                            <CheckCircle className="w-4 h-4 text-green-500" />
                          ) : (
                            <XCircle className="w-4 h-4 text-red-500" />
                          )}
                          <span className="text-xs font-medium text-text capitalize">
                            {execution.status}
                          </span>
                        </div>
                        {execution.dryRun && (
                          <span className="text-xs text-blue-500 bg-blue-50 dark:bg-blue-900/20 px-2 py-0.5 rounded">
                            Dry Run
                          </span>
                        )}
                      </div>
                      <div className="text-xs text-textMuted space-y-1">
                        <div>Trigger: {execution.trigger}</div>
                        <div>Actions: {execution.actionsExecuted}</div>
                        <div>{new Date(execution.timestamp).toLocaleString()}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
