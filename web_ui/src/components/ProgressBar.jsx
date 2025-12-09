import React from 'react';
import { motion } from 'framer-motion';

/**
 * Progress Bar Component
 * Shows visual progress with percentage and optional label
 */
export default function ProgressBar({
  progress = 0,
  label = null,
  showPercentage = true,
  variant = 'default',
  size = 'md'
}) {
  // Clamp progress between 0 and 100
  const clampedProgress = Math.min(Math.max(progress, 0), 100);

  // Variant colors
  const variants = {
    default: 'bg-blue-500',
    success: 'bg-green-500',
    warning: 'bg-yellow-500',
    error: 'bg-red-500',
    accent: 'bg-purple-500'
  };

  // Size classes
  const sizes = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3'
  };

  const bgColor = variants[variant] || variants.default;
  const height = sizes[size] || sizes.md;

  return (
    <div className="w-full">
      {/* Label and percentage */}
      {(label || showPercentage) && (
        <div className="flex justify-between items-center mb-1 text-sm">
          {label && <span className="text-gray-300 font-medium">{label}</span>}
          {showPercentage && (
            <span className="text-gray-400 font-mono">
              {Math.round(clampedProgress)}%
            </span>
          )}
        </div>
      )}

      {/* Progress bar container */}
      <div className={`w-full ${height} bg-gray-700 rounded-full overflow-hidden`}>
        {/* Animated progress fill */}
        <motion.div
          className={`${height} ${bgColor} rounded-full relative`}
          initial={{ width: 0 }}
          animate={{ width: `${clampedProgress}%` }}
          transition={{
            duration: 0.3,
            ease: 'easeOut'
          }}
        >
          {/* Shimmer effect for active progress */}
          {clampedProgress > 0 && clampedProgress < 100 && (
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-transparent via-white to-transparent opacity-30"
              animate={{
                x: ['-100%', '200%']
              }}
              transition={{
                duration: 1.5,
                repeat: Infinity,
                ease: 'linear'
              }}
            />
          )}
        </motion.div>
      </div>
    </div>
  );
}
