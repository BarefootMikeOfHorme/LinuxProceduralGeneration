import React from 'react';
import { Loader2 } from 'lucide-react';

/**
 * Loading Spinner Component
 * Reusable loading indicator with optional text
 */
export default function LoadingSpinner({
  size = 'md',
  text = null,
  className = ''
}) {
  const sizes = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12'
  };

  const spinnerSize = sizes[size] || sizes.md;

  if (text) {
    return (
      <div className={`flex flex-col items-center justify-center gap-3 ${className}`}>
        <Loader2 className={`${spinnerSize} text-blue-400 animate-spin`} />
        <p className="text-sm text-gray-400">{text}</p>
      </div>
    );
  }

  return (
    <Loader2 className={`${spinnerSize} text-blue-400 animate-spin ${className}`} />
  );
}
