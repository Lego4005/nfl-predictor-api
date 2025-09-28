import React, { useEffect, useRef } from 'react';
import { screenReaderUtils, focusUtils } from '@/utils/accessibility';

/**
 * Screen Reader Only component for hidden content that should be available to screen readers
 */
export const ScreenReaderOnly = ({ children, ...props }) => (
  <span 
    className="sr-only" 
    {...props}
    style={{
      position: 'absolute',
      width: '1px',
      height: '1px',
      padding: 0,
      margin: '-1px',
      overflow: 'hidden',
      clip: 'rect(0, 0, 0, 0)',
      whiteSpace: 'nowrap',
      border: 0
    }}
  >
    {children}
  </span>
);

/**
 * Live Region component for dynamic content announcements
 */
export const LiveRegion = ({ 
  children, 
  priority = 'polite', 
  atomic = true,
  role,
  ...props 
}) => (
  <div
    aria-live={priority}
    aria-atomic={atomic}
    role={role}
    className="sr-only"
    {...props}
  >
    {children}
  </div>
);

/**
 * Skip Navigation Link component
 */
export const SkipLink = ({ targetId, children = "Skip to main content" }) => (
  <a
    href={`#${targetId}`}
    className="skip-link"
    style={{
      position: 'absolute',
      top: '-40px',
      left: '6px',
      background: '#000',
      color: '#fff',
      padding: '8px',
      textDecoration: 'none',
      zIndex: 9999,
      borderRadius: '4px',
      transition: 'top 0.3s'
    }}
    onFocus={(e) => {
      e.target.style.top = '6px';
    }}
    onBlur={(e) => {
      e.target.style.top = '-40px';
    }}
  >
    {children}
  </a>
);

/**
 * Accessible Card component with proper focus management
 */
export const AccessibleCard = ({ 
  children, 
  onClick,
  isClickable = false,
  ariaLabel,
  ariaDescribedBy,
  role = 'region',
  tabIndex = isClickable ? 0 : undefined,
  className = '',
  ...props 
}) => {
  const cardRef = useRef(null);

  const handleKeyDown = (e) => {
    if (isClickable && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      if (onClick) onClick(e);
    }
  };

  return (
    <div
      ref={cardRef}
      role={role}
      tabIndex={tabIndex}
      className={`${className} ${isClickable ? 'cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2' : ''}`}
      onClick={isClickable ? onClick : undefined}
      onKeyDown={handleKeyDown}
      aria-label={ariaLabel}
      aria-describedby={ariaDescribedBy}
      {...props}
    >
      {children}
    </div>
  );
};

/**
 * Accessible Button component with loading states and proper ARIA attributes
 */
export const AccessibleButton = ({
  children,
  onClick,
  disabled = false,
  loading = false,
  ariaLabel,
  ariaDescribedBy,
  type = 'button',
  className = '',
  variant = 'primary',
  ...props
}) => {
  const baseClasses = 'inline-flex items-center justify-center px-4 py-2 text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variantClasses = {
    primary: 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500'
  };

  return (
    <button
      type={type}
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      onClick={onClick}
      disabled={disabled || loading}
      aria-label={ariaLabel}
      aria-describedby={ariaDescribedBy}
      aria-busy={loading}
      {...props}
    >
      {loading && (
        <svg
          className="animate-spin -ml-1 mr-2 h-4 w-4"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="4"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          />
        </svg>
      )}
      <ScreenReaderOnly>
        {loading ? 'Loading...' : ''}
      </ScreenReaderOnly>
      {children}
    </button>
  );
};

/**
 * Accessible Modal component with focus trapping
 */
export const AccessibleModal = ({
  isOpen,
  onClose,
  title,
  children,
  className = '',
  ...props
}) => {
  const modalRef = useRef(null);
  const previousFocusRef = useRef(null);

  useEffect(() => {
    if (isOpen) {
      previousFocusRef.current = document.activeElement;
      
      // Trap focus within modal
      if (modalRef.current) {
        focusUtils.trapFocus(modalRef.current);
      }
      
      // Prevent body scroll
      document.body.style.overflow = 'hidden';
      
      // Announce modal opening
      screenReaderUtils.announce(`Modal opened: ${title}`, 'assertive');
    } else {
      // Restore focus and body scroll
      document.body.style.overflow = 'unset';
      if (previousFocusRef.current) {
        focusUtils.restoreFocus(previousFocusRef.current);
      }
    }

    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, title]);

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      role="dialog"
      aria-modal="true"
      aria-labelledby="modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="fixed inset-0 bg-black bg-opacity-50" aria-hidden="true" />
      <div
        ref={modalRef}
        className={`relative bg-white rounded-lg shadow-xl max-w-md w-full mx-4 ${className}`}
        {...props}
      >
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 id="modal-title" className="text-lg font-semibold">
              {title}
            </h2>
            <AccessibleButton
              variant="secondary"
              onClick={onClose}
              ariaLabel="Close modal"
              className="p-1"
            >
              <svg
                className="w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </AccessibleButton>
          </div>
          {children}
        </div>
      </div>
    </div>
  );
};

/**
 * Accessible Table component with proper ARIA labels and keyboard navigation
 */
export const AccessibleTable = ({
  data,
  columns,
  caption,
  sortable = false,
  onSort,
  sortConfig,
  className = '',
  ...props
}) => {
  const handleSort = (columnKey) => {
    if (sortable && onSort) {
      onSort(columnKey);
      screenReaderUtils.announce(
        `Table sorted by ${columnKey} ${sortConfig?.direction === 'asc' ? 'ascending' : 'descending'}`,
        'polite'
      );
    }
  };

  const handleKeyDown = (e, columnKey) => {
    if (sortable && (e.key === 'Enter' || e.key === ' ')) {
      e.preventDefault();
      handleSort(columnKey);
    }
  };

  return (
    <div className="overflow-x-auto">
      <table
        className={`min-w-full ${className}`}
        role="table"
        {...props}
      >
        {caption && (
          <caption className="sr-only">
            {caption}
          </caption>
        )}
        <thead>
          <tr>
            {columns.map((column) => (
              <th
                key={column.key}
                scope="col"
                className={`px-4 py-2 text-left font-semibold ${
                  sortable ? 'cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500' : ''
                }`}
                tabIndex={sortable ? 0 : undefined}
                onClick={() => sortable && handleSort(column.key)}
                onKeyDown={(e) => handleKeyDown(e, column.key)}
                aria-sort={
                  sortable && sortConfig?.key === column.key
                    ? sortConfig.direction === 'asc'
                      ? 'ascending'
                      : 'descending'
                    : 'none'
                }
              >
                {column.header}
                {sortable && (
                  <span className="ml-1" aria-hidden="true">
                    {sortConfig?.key === column.key
                      ? sortConfig.direction === 'asc'
                        ? '↑'
                        : '↓'
                      : '↕'}
                  </span>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {columns.map((column) => (
                <td
                  key={column.key}
                  className="px-4 py-2"
                  role="cell"
                >
                  {column.cell ? column.cell(row) : row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

/**
 * Progress Bar component with ARIA attributes
 */
export const AccessibleProgressBar = ({
  value,
  max = 100,
  min = 0,
  label,
  className = '',
  ...props
}) => {
  const percentage = Math.round(((value - min) / (max - min)) * 100);

  return (
    <div className={`w-full ${className}`} {...props}>
      {label && (
        <div className="flex justify-between text-sm mb-1">
          <span>{label}</span>
          <span>{percentage}%</span>
        </div>
      )}
      <div
        className="w-full bg-gray-200 rounded-full h-2"
        role="progressbar"
        aria-valuenow={value}
        aria-valuemin={min}
        aria-valuemax={max}
        aria-label={label || `Progress: ${percentage}%`}
      >
        <div
          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
          style={{ width: `${percentage}%` }}
        />
      </div>
      <ScreenReaderOnly>
        Progress: {percentage}% complete
      </ScreenReaderOnly>
    </div>
  );
};

export {
  ScreenReaderOnly as default,
  LiveRegion,
  SkipLink,
  AccessibleCard,
  AccessibleButton,
  AccessibleModal,
  AccessibleTable,
  AccessibleProgressBar
};