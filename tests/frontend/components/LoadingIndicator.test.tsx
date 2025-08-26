/**
 * Tests for LoadingIndicator component
 */

import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import '@testing-library/jest-dom';
import LoadingIndicator from '../../../src/components/LoadingIndicator';

describe('LoadingIndicator', () => {
  it('renders nothing when isLoading is false', () => {
    const { container } = render(<LoadingIndicator isLoading={false} />);
    expect(container.firstChild).toBeNull();
  });

  it('renders loading indicator when isLoading is true', () => {
    render(<LoadingIndicator isLoading={true} />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('displays custom message when provided', () => {
    const customMessage = 'Fetching NFL data...';
    render(<LoadingIndicator isLoading={true} message={customMessage} />);
    
    expect(screen.getByText(customMessage)).toBeInTheDocument();
    expect(screen.queryByText('Loading...')).not.toBeInTheDocument();
  });

  it('renders progress bar when progress is provided', () => {
    render(<LoadingIndicator isLoading={true} progress={50} />);
    
    const progressBar = screen.getByText('50%').previousElementSibling;
    expect(progressBar).toBeInTheDocument();
    expect(progressBar?.firstElementChild).toHaveStyle({ width: '50%' });
  });

  it('handles progress value of 0', () => {
    render(<LoadingIndicator isLoading={true} progress={0} />);
    
    const progressBar = screen.getByText('0%').previousElementSibling;
    expect(progressBar?.firstElementChild).toHaveStyle({ width: '0%' });
  });

  it('handles progress value of 100', () => {
    render(<LoadingIndicator isLoading={true} progress={100} />);
    
    const progressBar = screen.getByText('100%').previousElementSibling;
    expect(progressBar?.firstElementChild).toHaveStyle({ width: '100%' });
  });

  it('clamps progress values above 100', () => {
    render(<LoadingIndicator isLoading={true} progress={150} />);
    
    const progressBar = screen.getByText('150%').previousElementSibling;
    expect(progressBar?.firstElementChild).toHaveStyle({ width: '100%' });
  });

  it('clamps progress values below 0', () => {
    render(<LoadingIndicator isLoading={true} progress={-10} />);
    
    const progressBar = screen.getByText('-10%').previousElementSibling;
    expect(progressBar?.firstElementChild).toHaveStyle({ width: '0%' });
  });

  it('applies small size styling correctly', () => {
    render(<LoadingIndicator isLoading={true} size="small" />);
    
    const container = screen.getByText('Loading...').parentElement;
    expect(container).toHaveStyle({ gap: '6px' });
    
    const text = screen.getByText('Loading...');
    expect(text).toHaveStyle({ fontSize: '12px' });
  });

  it('applies medium size styling correctly (default)', () => {
    render(<LoadingIndicator isLoading={true} size="medium" />);
    
    const container = screen.getByText('Loading...').parentElement;
    expect(container).toHaveStyle({ gap: '8px' });
    
    const text = screen.getByText('Loading...');
    expect(text).toHaveStyle({ fontSize: '14px' });
  });

  it('applies large size styling correctly', () => {
    render(<LoadingIndicator isLoading={true} size="large" />);
    
    const container = screen.getByText('Loading...').parentElement;
    expect(container).toHaveStyle({ gap: '12px' });
    
    const text = screen.getByText('Loading...');
    expect(text).toHaveStyle({ fontSize: '16px' });
  });

  it('uses medium size as default when size not specified', () => {
    render(<LoadingIndicator isLoading={true} />);
    
    const text = screen.getByText('Loading...');
    expect(text).toHaveStyle({ fontSize: '14px' });
  });

  it('includes CSS animation for spinner', () => {
    render(<LoadingIndicator isLoading={true} />);
    
    // Check that the style tag with animation is present
    const styleTag = document.querySelector('style');
    expect(styleTag?.textContent).toContain('@keyframes spin');
    expect(styleTag?.textContent).toContain('transform: rotate(0deg)');
    expect(styleTag?.textContent).toContain('transform: rotate(360deg)');
  });

  it('renders both message and progress when both provided', () => {
    const message = 'Processing data...';
    render(<LoadingIndicator isLoading={true} message={message} progress={75} />);
    
    expect(screen.getByText(message)).toBeInTheDocument();
    expect(screen.getByText('75%')).toBeInTheDocument();
  });

  it('has proper accessibility structure', () => {
    render(<LoadingIndicator isLoading={true} message="Loading data" />);
    
    const container = screen.getByText('Loading data').parentElement;
    expect(container).toHaveStyle({
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    });
  });

  it('handles decimal progress values correctly', () => {
    render(<LoadingIndicator isLoading={true} progress={33.7} />);
    
    expect(screen.getByText('34%')).toBeInTheDocument(); // Should round
    
    const progressBar = screen.getByText('34%').previousElementSibling;
    expect(progressBar?.firstElementChild).toHaveStyle({ width: '33.7%' });
  });

  it('renders spinner with correct styling', () => {
    render(<LoadingIndicator isLoading={true} />);
    
    const text = screen.getByText('Loading...');
    const spinner = text.previousElementSibling;
    
    expect(spinner).toHaveStyle({
      borderRadius: '50%',
      animation: 'spin 1s linear infinite'
    });
  });

  it('maintains consistent styling across different props combinations', () => {
    const { rerender } = render(
      <LoadingIndicator isLoading={true} message="Test" size="small" />
    );
    
    expect(screen.getByText('Test')).toHaveStyle({ fontSize: '12px' });
    
    rerender(
      <LoadingIndicator isLoading={true} message="Test" size="large" progress={50} />
    );
    
    expect(screen.getByText('Test')).toHaveStyle({ fontSize: '16px' });
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('handles empty message string', () => {
    render(<LoadingIndicator isLoading={true} message="" />);
    
    // Should still render the container but with empty text
    const container = document.querySelector('[style*="display: flex"]');
    expect(container).toBeInTheDocument();
  });

  it('handles undefined progress gracefully', () => {
    render(<LoadingIndicator isLoading={true} progress={undefined} />);
    
    expect(screen.getByText('Loading...')).toBeInTheDocument();
    expect(screen.queryByText('%')).not.toBeInTheDocument();
  });
});