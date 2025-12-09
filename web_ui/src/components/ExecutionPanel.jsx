import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Loader2, CheckCircle, XCircle, AlertCircle, Play } from 'lucide-react';
import ProgressBar from './ProgressBar';
import { useWorkflowStore } from '../store/workflowStore';

/**
 * Execution Panel Component
 * Shows real-time execution status, progress, and current node
 */
export default function ExecutionPanel() {
  const {
    isExecuting,
    executionProgress,
    executionResults,
    currentExecutingNode
  } = useWorkflowStore();

  // Determine status
  const getStatus = () => {
    if (isExecuting) return 'running';
    if (executionResults?.error) return 'error';
    if (executionProgress === 100 && !isExecuting) return 'completed';
    return 'idle';
  };

  const status = getStatus();

  // Status configurations
  const statusConfig = {
    idle: {
      icon: Play,
      color: 'text-gray-400',
      bgColor: 'bg-gray-700/50',
      label: 'Ready to execute'
    },
    running: {
      icon: Loader2,
      color: 'text-blue-400',
      bgColor: 'bg-blue-900/30',
      label: 'Executing workflow...',
      animate: true
    },
    completed: {
      icon: CheckCircle,
      color: 'text-green-400',
      bgColor: 'bg-green-900/30',
      label: 'Execution completed'
    },
    error: {
      icon: XCircle,
      color: 'text-red-400',
      bgColor: 'bg-red-900/30',
      label: 'Execution failed'
    }
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  // Don't show panel when idle
  if (status === 'idle' && executionProgress === 0) {
    return null;
  }

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        className={`
          fixed top-16 right-4 w-96
          ${config.bgColor}
          backdrop-blur-lg
          border border-gray-700
          rounded-lg shadow-2xl
          p-4 z-50
        `}
      >
        {/* Header */}
        <div className="flex items-center gap-3 mb-3">
          <div className={`${config.color}`}>
            {config.animate ? (
              <Icon className="w-5 h-5 animate-spin" />
            ) : (
              <Icon className="w-5 h-5" />
            )}
          </div>
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-gray-100">
              {config.label}
            </h3>
            {currentExecutingNode && (
              <p className="text-xs text-gray-400 mt-0.5">
                Node: <span className="font-mono">{currentExecutingNode}</span>
              </p>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        {(status === 'running' || status === 'completed') && (
          <div className="mb-3">
            <ProgressBar
              progress={executionProgress}
              variant={status === 'completed' ? 'success' : 'default'}
              size="md"
              showPercentage={true}
            />
          </div>
        )}

        {/* Execution Details */}
        {status === 'running' && (
          <div className="bg-black/30 rounded p-2 mb-2">
            <div className="flex items-center gap-2 text-xs text-gray-400">
              <div className="flex gap-1">
                <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse" />
                <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
                <div className="w-1.5 h-1.5 bg-blue-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
              </div>
              <span>Processing nodes...</span>
            </div>
          </div>
        )}

        {/* Completed Details */}
        {status === 'completed' && executionResults && (
          <div className="bg-black/30 rounded p-2 mb-2">
            <div className="text-xs text-gray-300 space-y-1">
              {executionResults.nodes_executed && (
                <div>
                  ✓ <span className="font-semibold">{executionResults.nodes_executed}</span> nodes executed
                </div>
              )}
              {executionResults.previews && (
                <div>
                  ✓ <span className="font-semibold">{Object.keys(executionResults.previews).length}</span> previews generated
                </div>
              )}
            </div>
          </div>
        )}

        {/* Error Details */}
        {status === 'error' && executionResults?.error && (
          <div className="bg-red-900/20 border border-red-700/50 rounded p-3">
            <div className="flex items-start gap-2">
              <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="text-sm text-red-300 font-medium mb-1">
                  {executionResults.error.error || 'Execution Error'}
                </p>
                <p className="text-xs text-red-400">
                  {executionResults.error.message || 'An error occurred during execution'}
                </p>
                {executionResults.error.recovery_steps && (
                  <div className="mt-2 text-xs text-red-300">
                    <div className="font-medium mb-1">Try this:</div>
                    <ul className="list-disc list-inside space-y-0.5">
                      {executionResults.error.recovery_steps.slice(0, 2).map((step, i) => (
                        <li key={i}>{step}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Timing */}
        {status === 'running' && (
          <div className="text-xs text-gray-500 text-center">
            Execution in progress...
          </div>
        )}
      </motion.div>
    </AnimatePresence>
  );
}
