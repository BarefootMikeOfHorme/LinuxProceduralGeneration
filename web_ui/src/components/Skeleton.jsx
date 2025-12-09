import React from 'react';

/**
 * Skeleton Component
 * Shows animated loading placeholders
 */
export default function Skeleton({
  width = 'w-full',
  height = 'h-4',
  rounded = 'rounded',
  className = ''
}) {
  return (
    <div
      className={`
        ${width} ${height} ${rounded}
        bg-gray-700 animate-pulse
        ${className}
      `}
    />
  );
}

/**
 * Skeleton variants for common use cases
 */
export function SkeletonText({ lines = 3, className = '' }) {
  return (
    <div className={`space-y-2 ${className}`}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          width={i === lines - 1 ? 'w-3/4' : 'w-full'}
          height="h-3"
        />
      ))}
    </div>
  );
}

export function SkeletonCard({ className = '' }) {
  return (
    <div className={`bg-gray-800 rounded-lg p-4 ${className}`}>
      <Skeleton width="w-1/3" height="h-6" className="mb-3" />
      <SkeletonText lines={3} />
    </div>
  );
}

export function SkeletonAvatar({ size = 'w-10 h-10', className = '' }) {
  return (
    <Skeleton
      width={size.split(' ')[0]}
      height={size.split(' ')[1]}
      rounded="rounded-full"
      className={className}
    />
  );
}
