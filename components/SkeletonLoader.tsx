import React from 'react';

interface SkeletonLoaderProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  lines?: number;
}

/**
 * Skeleton loader component for better loading UX
 */
export const SkeletonLoader: React.FC<SkeletonLoaderProps> = ({
  className = '',
  variant = 'rectangular',
  width,
  height,
  lines,
}) => {
  const baseClasses = 'animate-pulse bg-slate-800 rounded';
  
  const variantClasses = {
    text: 'h-4',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  };

  if (lines && lines > 1) {
    return (
      <div className={`space-y-2 ${className}`}>
        {Array.from({ length: lines }).map((_, i) => (
          <div
            key={i}
            className={`${baseClasses} ${variantClasses.text}`}
            style={{
              width: i === lines - 1 ? '80%' : '100%',
              height: height || '1rem',
            }}
            aria-hidden="true"
          />
        ))}
      </div>
    );
  }

  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === 'number' ? `${width}px` : width;
  if (height) style.height = typeof height === 'number' ? `${height}px` : height;

  return (
    <div
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={style}
      aria-hidden="true"
      aria-label="Loading"
    />
  );
};

/**
 * Card skeleton for report cards
 */
export const CardSkeleton: React.FC = () => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 animate-pulse">
      <div className="flex justify-between items-center mb-4 border-b border-slate-800 pb-3">
        <div className="flex-1">
          <SkeletonLoader variant="rectangular" width="120px" height="24px" className="mb-2" />
          <SkeletonLoader variant="text" width="200px" height="12px" />
        </div>
        <SkeletonLoader variant="rectangular" width="60px" height="20px" />
      </div>
      <div className="space-y-3">
        <SkeletonLoader lines={2} />
        <SkeletonLoader lines={3} />
        <SkeletonLoader lines={2} />
      </div>
    </div>
  );
};

/**
 * Chart skeleton
 */
export const ChartSkeleton: React.FC = () => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-xl p-4">
      <SkeletonLoader variant="text" width="150px" height="12px" className="mb-4" />
      <SkeletonLoader variant="rectangular" width="100%" height="192px" />
    </div>
  );
};

