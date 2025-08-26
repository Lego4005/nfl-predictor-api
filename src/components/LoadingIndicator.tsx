import React from 'react';
import { LoadingIndicatorProps } from '../types/ui.types';

const LoadingIndicator: React.FC<LoadingIndicatorProps> = ({
  isLoading,
  message = 'Loading...',
  progress,
  size = 'medium'
}) => {
  if (!isLoading) {
    return null;
  }

  const getSizeStyles = () => {
    switch (size) {
      case 'small':
        return {
          spinner: { width: '16px', height: '16px', borderWidth: '2px' },
          text: { fontSize: '12px' },
          container: { gap: '6px' }
        };
      case 'large':
        return {
          spinner: { width: '32px', height: '32px', borderWidth: '3px' },
          text: { fontSize: '16px' },
          container: { gap: '12px' }
        };
      case 'medium':
      default:
        return {
          spinner: { width: '20px', height: '20px', borderWidth: '2px' },
          text: { fontSize: '14px' },
          container: { gap: '8px' }
        };
    }
  };

  const sizeStyles = getSizeStyles();

  const spinnerStyle = {
    ...sizeStyles.spinner,
    border: `${sizeStyles.spinner.borderWidth} solid #f3f4f6`,
    borderTop: `${sizeStyles.spinner.borderWidth} solid #3b82f6`,
    borderRadius: '50%',
    animation: 'spin 1s linear infinite'
  };

  const containerStyle = {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    flexDirection: 'column' as const,
    ...sizeStyles.container,
    padding: '16px'
  };

  const textStyle = {
    color: '#6b7280',
    fontWeight: '500' as const,
    ...sizeStyles.text
  };

  return (
    <>
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
      
      <div style={containerStyle}>
        <div style={spinnerStyle}></div>
        
        <div style={textStyle}>
          {message}
        </div>

        {progress !== undefined && (
          <div style={{
            width: '200px',
            height: '4px',
            backgroundColor: '#f3f4f6',
            borderRadius: '2px',
            overflow: 'hidden',
            marginTop: '8px'
          }}>
            <div
              style={{
                width: `${Math.min(100, Math.max(0, progress))}%`,
                height: '100%',
                backgroundColor: '#3b82f6',
                borderRadius: '2px',
                transition: 'width 0.3s ease'
              }}
            />
          </div>
        )}

        {progress !== undefined && (
          <div style={{
            fontSize: '12px',
            color: '#9ca3af',
            marginTop: '4px'
          }}>
            {Math.round(progress)}%
          </div>
        )}
      </div>
    </>
  );
};

export default LoadingIndicator;