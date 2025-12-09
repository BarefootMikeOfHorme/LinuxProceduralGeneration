/**
 * Notification Utility
 * Provides a clean API for showing toast notifications throughout the app
 * Replaces all browser alert() calls with proper notifications
 */

import toast from 'react-hot-toast';

/**
 * Show a success notification
 * @param {string} message - The message to display
 * @param {object} options - Additional options
 */
export const notifySuccess = (message, options = {}) => {
  return toast.success(message, {
    duration: 3000,
    position: 'top-right',
    style: {
      background: '#10b981',
      color: '#fff',
      borderRadius: '8px',
      padding: '12px 16px',
      fontWeight: '500',
    },
    iconTheme: {
      primary: '#fff',
      secondary: '#10b981',
    },
    ...options,
  });
};

/**
 * Show an error notification
 * @param {string} message - The error message
 * @param {object} details - Error details object (optional)
 * @param {object} options - Additional options
 */
export const notifyError = (message, details = null, options = {}) => {
  // If we have structured error details from backend, show recovery steps
  if (details && details.recovery_steps) {
    return toast.error(
      (t) => (
        <div>
          <div className="font-semibold mb-1">{details.error || 'Error'}</div>
          <div className="text-sm mb-2">{details.message || message}</div>
          {details.recovery_steps && details.recovery_steps.length > 0 && (
            <div className="text-xs mt-2 border-t border-white/20 pt-2">
              <div className="font-medium mb-1">Try this:</div>
              <ul className="list-disc list-inside space-y-1">
                {details.recovery_steps.slice(0, 2).map((step, i) => (
                  <li key={i}>{step}</li>
                ))}
              </ul>
            </div>
          )}
          <button
            onClick={() => toast.dismiss(t.id)}
            className="mt-2 text-xs underline"
          >
            Dismiss
          </button>
        </div>
      ),
      {
        duration: 6000,
        position: 'top-right',
        style: {
          background: '#ef4444',
          color: '#fff',
          borderRadius: '8px',
          padding: '12px 16px',
          maxWidth: '420px',
        },
        ...options,
      }
    );
  }

  // Simple error notification
  return toast.error(message, {
    duration: 4000,
    position: 'top-right',
    style: {
      background: '#ef4444',
      color: '#fff',
      borderRadius: '8px',
      padding: '12px 16px',
      fontWeight: '500',
    },
    iconTheme: {
      primary: '#fff',
      secondary: '#ef4444',
    },
    ...options,
  });
};

/**
 * Show a warning notification
 * @param {string} message - The warning message
 * @param {object} options - Additional options
 */
export const notifyWarning = (message, options = {}) => {
  return toast(message, {
    duration: 4000,
    position: 'top-right',
    icon: '⚠️',
    style: {
      background: '#f59e0b',
      color: '#fff',
      borderRadius: '8px',
      padding: '12px 16px',
      fontWeight: '500',
    },
    ...options,
  });
};

/**
 * Show an info notification
 * @param {string} message - The info message
 * @param {object} options - Additional options
 */
export const notifyInfo = (message, options = {}) => {
  return toast(message, {
    duration: 3000,
    position: 'top-right',
    icon: 'ℹ️',
    style: {
      background: '#3b82f6',
      color: '#fff',
      borderRadius: '8px',
      padding: '12px 16px',
      fontWeight: '500',
    },
    ...options,
  });
};

/**
 * Show a loading notification
 * Returns a function to dismiss it
 * @param {string} message - The loading message
 */
export const notifyLoading = (message) => {
  return toast.loading(message, {
    position: 'top-right',
    style: {
      background: '#6b7280',
      color: '#fff',
      borderRadius: '8px',
      padding: '12px 16px',
      fontWeight: '500',
    },
  });
};

/**
 * Update an existing notification
 * @param {string} toastId - ID returned from notifyLoading
 * @param {string} message - New message
 * @param {string} type - 'success' or 'error'
 */
export const updateNotification = (toastId, message, type = 'success') => {
  const style = {
    background: type === 'success' ? '#10b981' : '#ef4444',
    color: '#fff',
    borderRadius: '8px',
    padding: '12px 16px',
    fontWeight: '500',
  };

  if (type === 'success') {
    toast.success(message, { id: toastId, style });
  } else {
    toast.error(message, { id: toastId, style });
  }
};

/**
 * Dismiss a specific notification
 * @param {string} toastId - ID of the toast to dismiss
 */
export const dismissNotification = (toastId) => {
  toast.dismiss(toastId);
};

/**
 * Dismiss all notifications
 */
export const dismissAllNotifications = () => {
  toast.dismiss();
};

/**
 * Show a custom notification with full control
 * @param {function|string} content - Content to display
 * @param {object} options - Toast options
 */
export const notifyCustom = (content, options = {}) => {
  return toast.custom(content, {
    position: 'top-right',
    ...options,
  });
};

/**
 * Show help dialog as a notification (replaces alert for keyboard shortcuts)
 * @param {string} title - Help dialog title
 * @param {array} shortcuts - Array of {key, action} objects
 */
export const showHelpDialog = (title, shortcuts) => {
  return toast(
    (t) => (
      <div className="w-full">
        <div className="font-bold text-lg mb-3 text-gray-900">{title}</div>
        <div className="space-y-2">
          {shortcuts.map((shortcut, i) => (
            <div key={i} className="flex justify-between items-center text-sm">
              <span className="text-gray-700">{shortcut.action}</span>
              <kbd className="px-2 py-1 bg-gray-700 text-white rounded text-xs font-mono">
                {shortcut.key}
              </kbd>
            </div>
          ))}
        </div>
        <button
          onClick={() => toast.dismiss(t.id)}
          className="mt-4 w-full bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded font-medium text-sm"
        >
          Got it!
        </button>
      </div>
    ),
    {
      duration: Infinity, // Stay until dismissed
      position: 'top-center',
      style: {
        background: '#fff',
        color: '#000',
        borderRadius: '12px',
        padding: '20px',
        maxWidth: '400px',
        boxShadow: '0 10px 40px rgba(0,0,0,0.2)',
      },
      icon: '❓',
    }
  );
};
