import { useAuthStore } from '../../store/useAuthStore';
import { Bell, Menu, Zap } from 'lucide-react';
import { useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';

export function Header() {
    const { student, logout } = useAuthStore();
    const navigate = useNavigate();
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    return (
        <>
            <header className="flex h-16 items-center justify-between border-b border-slate-200 bg-white/80 backdrop-blur-md px-4 md:px-6 shadow-sm z-10">
                <div className="flex items-center gap-3">
                    {/* Mobile menu toggle */}
                    <button
                        onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                        className="p-2 rounded-lg text-slate-500 hover:bg-slate-100 md:hidden"
                    >
                        <Menu className="h-5 w-5" />
                    </button>

                    <div className="md:hidden flex items-center gap-2">
                        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-600">
                            <Zap className="h-3.5 w-3.5 text-white" />
                        </div>
                        <span className="font-bold text-blue-600">ICAN</span>
                    </div>

                    <h2 className="hidden md:block text-lg font-semibold text-slate-800">
                        Welcome back, {student?.name || 'Student'}
                    </h2>
                </div>

                <div className="flex items-center gap-3">
                    {/* XP Badge */}
                    <div className="hidden sm:flex items-center gap-1.5 rounded-full bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 px-3 py-1.5">
                        <Zap className="h-3.5 w-3.5 text-amber-500" />
                        <span className="text-xs font-bold text-amber-700">{student?.xp || 0} XP</span>
                    </div>

                    <button className="relative rounded-full p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 transition-colors">
                        <Bell className="h-5 w-5" />
                        <span className="absolute -top-0.5 -right-0.5 h-3 w-3 rounded-full bg-blue-500 border-2 border-white" />
                    </button>

                    <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
                        <div className="h-8 w-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-xs shadow-md">
                            {student?.name?.charAt(0) || 'S'}
                        </div>
                        <span className="hidden md:block text-sm font-medium text-slate-700">
                            {student?.name || 'Guest'}
                        </span>
                    </div>
                </div>
            </header>

            {/* Mobile Navigation */}
            {mobileMenuOpen && (
                <div className="md:hidden bg-white border-b border-slate-200 shadow-lg z-20">
                    <nav className="grid grid-cols-4 gap-1 p-2">
                        {[
                            { name: 'Home', href: '/dashboard', icon: '🏠' },
                            { name: 'Learn', href: '/subjects', icon: '📚' },
                            { name: 'Quiz', href: '/quiz', icon: '🎯' },
                            { name: 'Videos', href: '/videos', icon: '🎬' },
                        ].map((item) => (
                            <NavLink
                                key={item.name}
                                to={item.href}
                                onClick={() => setMobileMenuOpen(false)}
                                className="flex flex-col items-center gap-1 rounded-xl p-2 text-slate-600 hover:bg-blue-50 hover:text-blue-600 transition-colors"
                            >
                                <span className="text-lg">{item.icon}</span>
                                <span className="text-[10px] font-medium">{item.name}</span>
                            </NavLink>
                        ))}
                    </nav>
                </div>
            )}
        </>
    );
}
