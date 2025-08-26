import React from 'react';
import { RetryButtonProps } from '../types/ui.types';

const RetryButton: React.FC<RetryButtonProps> = ({
  onRetry,
  isRetrying,
  disabled = false,
  variant = 'primary'
}) => {
  const getButtonStyle = () => {
    const baseStyle = {
      padding: '8px 16px',
      borderRadius: '6px',
      border: 'none',
      cursor: disabled || isRetrying ? 'not-allowed' : 'pointer',
      fontSize: '14px',
      fontWeight: '500' as const,
      display: 'flex',
      alignItems: 'center',
      gap: '6px',
      transition: 'all 0.2s ease',
      opacity: disabled ? 0.5 : 1
    };

    if (variant === 'primary') {
      return {
        ...baseStyle,
        backgroundColor: '#3b82f6',
        color: 'white',
        ':hover': !disabled && !isRetrying ? {
          backgroundColor: '#2563eb'
        } : {}
      };
    } else {
      return {
        ...baseStyle,
        backgroundColor: 'transparent',
        color: '#3b82f6',
        border: '1px solid #3b82f6',
        ':hover': !disabled && !isRetrying ? {
          backgroundColor: '#eff6ff'
        } : {}
      };
    }
  };

  const handleClick = () => {
    if (!disabled && !isRetrying) {
      onRetry();
    }
  };

  return (
    <button
      onClick={handleClick}
      disabled={disabled || isRetrying}
      style={getButtonStyle()}
    >
      {isRetrying ? (
        <>
          <div style={{
            width: '14px',
            height: '14px',
            border: '2px solid transparent',
            borderTop: '2px solid currentColor',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }} />
          <span>Retrying...</span>
        </>
      ) : (
        <>
          <span>🔄</span>
          <span>Retry</span>
        </>
      )}
      
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </button>
  );
};

export default RetryButton;