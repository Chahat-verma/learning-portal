import clsx from 'clsx';

interface ProgressBarProps {
    progress: number;
    className?: string;
    color?: 'blue' | 'green' | 'yellow' | 'red';
    size?: 'sm' | 'md' | 'lg';
    showLabel?: boolean;
}

const colorMap = {
    blue: 'bg-blue-600',
    green: 'bg-green-600',
    yellow: 'bg-yellow-500',
    red: 'bg-red-500',
};

const sizeMap = {
    sm: 'h-1.5',
    md: 'h-2.5',
    lg: 'h-4',
};

export function ProgressBar({ progress, className, color = 'blue', size = 'md', showLabel = false }: ProgressBarProps) {
    const clampedProgress = Math.min(100, Math.max(0, progress));

    return (
        <div className={clsx('w-full', className)}>
            {showLabel && (
                <div className="mb-1 flex justify-between text-xs font-medium text-slate-500">
                    <span>Progress</span>
                    <span>{Math.round(clampedProgress)}%</span>
                </div>
            )}
            <div className={clsx('w-full overflow-hidden rounded-full bg-slate-200', sizeMap[size])}>
                <div
                    className={clsx('transition-all duration-500 ease-out', colorMap[color], sizeMap[size])}
                    style={{ width: `${clampedProgress}%` }}
                />
            </div>
        </div>
    );
}
