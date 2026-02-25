import { NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, BookOpen, GraduationCap, PlayCircle, LogOut, Zap, Activity } from 'lucide-react';
import clsx from 'clsx';
import { useAuthStore } from '../../store/useAuthStore';

const navigation = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Subjects', href: '/subjects', icon: BookOpen },
    { name: 'Quiz Mode', href: '/quiz', icon: GraduationCap },
    { name: 'Video Library', href: '/videos', icon: PlayCircle },
];

export function Sidebar() {
    const { student, logout } = useAuthStore();
    const navigate = useNavigate();

    const handleLogout = () => {
        logout();
        navigate('/');
    };

    const xpPercent = Math.min(((student?.xp || 0) % 100), 100);

    return (
        <div className="hidden md:flex h-full w-64 flex-col bg-gradient-to-b from-slate-900 via-blue-950 to-slate-900 text-white shadow-2xl">
            {/* Brand */}
            <div className="flex h-16 items-center gap-2.5 px-6 border-b border-white/10">
                <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg shadow-blue-500/30 animate-glow">
                    <Zap className="h-4.5 w-4.5 text-white" />
                </div>
                <h1 className="text-xl font-black tracking-wider gradient-text">
                    ICAN
                </h1>
            </div>

            {/* Student Info */}
            {student && (
                <div className="mx-4 mt-5 rounded-2xl bg-white/5 backdrop-blur-sm border border-white/10 p-4">
                    <div className="flex items-center gap-3">
                        <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 text-white font-black text-sm shadow-lg shadow-blue-500/20">
                            {student.name?.charAt(0) || 'S'}
                        </div>
                        <div className="min-w-0">
                            <p className="text-sm font-bold text-white truncate">{student.name}</p>
                            <p className="text-xs text-blue-300 font-medium">
                                Level {student.level || 1} • {student.xp || 0} XP
                            </p>
                        </div>
                    </div>
                    {/* XP Bar with shimmer */}
                    <div className="mt-3 h-1.5 rounded-full bg-white/10 overflow-hidden relative">
                        <div
                            className="h-full rounded-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-700"
                            style={{ width: `${xpPercent}%` }}
                        />
                        <div className="absolute inset-0 animate-shimmer rounded-full" />
                    </div>
                    <p className="text-[10px] text-blue-400/60 mt-1.5">{xpPercent}% to next level</p>
                </div>
            )}

            {/* Navigation */}
            <nav className="flex-1 space-y-1 px-3 py-5">
                {navigation.map((item) => (
                    <NavLink
                        key={item.name}
                        to={item.href}
                        className={({ isActive }) =>
                            clsx(
                                'group flex items-center rounded-xl px-3 py-2.5 text-sm font-semibold transition-all duration-200',
                                isActive
                                    ? 'bg-gradient-to-r from-blue-600/80 to-indigo-600/60 text-white shadow-lg shadow-blue-500/15'
                                    : 'text-slate-400 hover:bg-white/8 hover:text-white'
                            )
                        }
                    >
                        <item.icon className="mr-3 h-5 w-5 flex-shrink-0 transition-transform group-hover:scale-110" aria-hidden="true" />
                        {item.name}
                    </NavLink>
                ))}
            </nav>

            {/* System Status */}
            <div className="mx-4 mb-3 rounded-xl bg-emerald-500/8 border border-emerald-400/15 p-3.5">
                <div className="flex items-center gap-2 mb-2">
                    <Activity className="h-3.5 w-3.5 text-emerald-400" />
                    <span className="text-xs font-bold text-emerald-300">System Live</span>
                </div>
                <div className="flex items-center gap-3">
                    {['Ollama', 'RAG', 'ChromaDB'].map((s) => (
                        <div key={s} className="flex items-center gap-1.5">
                            <div className="relative">
                                <div className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                                <div className="absolute inset-0 h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping opacity-30" />
                            </div>
                            <span className="text-[10px] text-emerald-400/80 font-medium">{s}</span>
                        </div>
                    ))}
                </div>
            </div>

            {/* Logout */}
            <div className="border-t border-white/10 p-3">
                <button
                    onClick={handleLogout}
                    className="group flex w-full items-center rounded-xl px-3 py-2.5 text-sm font-semibold text-slate-500 transition-all hover:bg-red-500/10 hover:text-red-400"
                >
                    <LogOut className="mr-3 h-5 w-5 transition-transform group-hover:scale-110" />
                    Logout
                </button>
            </div>
        </div>
    );
}
