import type { LucideIcon } from 'lucide-react';
import clsx from 'clsx';

interface StatsCardProps {
    label: string;
    value: string | number;
    icon: LucideIcon;
    trend?: string;
    trendUp?: boolean;
    color?: 'blue' | 'green' | 'purple' | 'orange';
}

const colorMap = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    orange: 'bg-orange-500',
};

export function StatsCard({ label, value, icon: Icon, trend, trendUp, color = 'blue' }: StatsCardProps) {
    return (
        <div className="rounded-xl bg-white p-6 shadow-sm border border-slate-100">
            <div className="flex items-center justify-between">
                <div>
                    <p className="text-sm font-medium text-slate-500">{label}</p>
                    <p className="mt-2 text-3xl font-bold text-slate-800">{value}</p>
                </div>
                <div className={clsx('rounded-full p-3 text-white shadow-lg', colorMap[color])}>
                    <Icon className="h-6 w-6" />
                </div>
            </div>
            {trend && (
                <div className="mt-4 flex items-center text-sm">
                    <span className={clsx('font-medium', trendUp ? 'text-green-600' : 'text-red-600')}>
                        {trend}
                    </span>
                    <span className="ml-2 text-slate-400">vs last week</span>
                </div>
            )}
        </div>
    );
}
