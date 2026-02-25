import clsx from 'clsx';

interface DifficultyIndicatorProps {
    level: 'easy' | 'medium' | 'hard';
    className?: string;
}

const colorMap = {
    easy: 'bg-green-100 text-green-700 border-green-200',
    medium: 'bg-yellow-100 text-yellow-700 border-yellow-200',
    hard: 'bg-red-100 text-red-700 border-red-200',
};

export function DifficultyIndicator({ level, className }: DifficultyIndicatorProps) {
    return (
        <span
            className={clsx(
                'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize',
                colorMap[level],
                className
            )}
        >
            {level}
        </span>
    );
}
