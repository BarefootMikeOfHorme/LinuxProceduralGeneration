/**
 * VaultMind Forge - HoloPanel Component
 * Holographic glassmorphism panel with functional colors
 *
 * NOT WIRED UP YET - Ready for integration
 */

import React from 'react';
import '../../styles/fui-theme.css';

export interface HoloPanelProps {
  /** Color theme (maps to functional meaning) */
  color?: 'cyan' | 'magenta' | 'yellow' | 'green' | 'red' | 'dim';

  /** Optional panel title */
  title?: string;

  /** Content */
  children: React.ReactNode;

  /** Enable stronger glow effect */
  glow?: boolean;

  /** Additional CSS classes */
  className?: string;

  /** Inline styles */
  style?: React.CSSProperties;

  /** Click handler */
  onClick?: () => void;
}

/**
 * HoloPanel - Glassmorphism panel with functional color coding
 *
 * Color meanings:
 * - cyan: Data/System Status
 * - magenta: Configuration
 * - yellow: Processing/Generation
 * - green: Success/Output
 * - red: Errors
 *
 * @example
 * <HoloPanel color="cyan" title="System Status">
 *   <p>CPU: 45%</p>
 * </HoloPanel>
 */
export const HoloPanel: React.FC<HoloPanelProps> = ({
  color = 'cyan',
  title,
  children,
  glow = false,
  className = '',
  style,
  onClick,
}) => {
  const panelClasses = [
    'holo-panel',
    `holo-${color}`,
    glow ? 'glow' : '',
    className,
  ].filter(Boolean).join(' ');

  return (
    <div
      className={panelClasses}
      style={style}
      onClick={onClick}
    >
      {title && (
        <div className="holo-panel-title">
          {title}
        </div>
      )}
      <div className="holo-panel-content">
        {children}
      </div>
    </div>
  );
};

/**
 * Usage Examples:
 *
 * // System status panel
 * <HoloPanel color="cyan" title="SYSTEM STATUS">
 *   <StatusIndicator type="cpu" value={45} />
 * </HoloPanel>
 *
 * // Workflow config panel
 * <HoloPanel color="magenta" title="WORKFLOW CONFIG">
 *   <ConfigForm />
 * </HoloPanel>
 *
 * // Processing indicator
 * <HoloPanel color="yellow" title="GENERATING" glow>
 *   <ProgressBar value={75} />
 * </HoloPanel>
 *
 * // Success output
 * <HoloPanel color="green" title="OUTPUT">
 *   <ImagePreview src="output.png" />
 * </HoloPanel>
 *
 * // Error panel
 * <HoloPanel color="red" title="ERROR">
 *   <ErrorMessage error={error} />
 * </HoloPanel>
 */

export default HoloPanel;
