import clsx from 'clsx';

interface SkeletonProps {
    className?: string;
    variant?: 'text' | 'circular' | 'rectangular';
    width?: string | number;
    height?: string | number;
}

export function LoadingSkeleton({ className, variant = 'text', width, height }: SkeletonProps) {
    return (
        <div
            className={clsx(
                'animate-pulse bg-slate-200',
                {
                    'rounded-md': variant === 'text' || variant === 'rectangular',
                    'rounded-full': variant === 'circular',
                },
                className
            )}
            style={{ width, height }}
        />
    );
}
