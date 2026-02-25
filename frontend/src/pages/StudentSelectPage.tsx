import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';
import api from '../services/api';
import { Zap, Star, TrendingUp } from 'lucide-react';

interface DemoStudent {
    student_id: string;
    display_name: string;
    difficulty: string;
    xp: number;
    level: number;
    description: string;
}

const DIFFICULTY_CONFIG: Record<string, { gradient: string; badge: string; ring: string }> = {
    easy: { gradient: 'from-emerald-400 to-teal-500', badge: 'bg-emerald-100 text-emerald-700', ring: 'ring-emerald-400/30' },
    medium: { gradient: 'from-amber-400 to-orange-500', badge: 'bg-amber-100 text-amber-700', ring: 'ring-amber-400/30' },
    hard: { gradient: 'from-rose-400 to-red-500', badge: 'bg-red-100 text-red-700', ring: 'ring-rose-400/30' },
};

const AVATARS = ['🎓', '🚀', '⭐'];

export function StudentSelectPage() {
    const navigate = useNavigate();
    const { login } = useAuthStore();
    const [students, setStudents] = useState<DemoStudent[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedId, setSelectedId] = useState<string | null>(null);

    useEffect(() => {
        const fetchStudents = async () => {
            try {
                const res = await api.get<DemoStudent[]>('/demo/students');
                setStudents(res.data);
            } catch (err) {
                console.error('Failed to fetch demo students:', err);
                setError('Could not load student profiles. Using defaults.');
                setStudents([
                    { student_id: 'struggling_student', display_name: 'Riya (Struggling)', difficulty: 'easy', xp: 45, level: 1, description: 'Needs extra support' },
                    { student_id: 'average_student', display_name: 'Arjun (Average)', difficulty: 'medium', xp: 480, level: 5, description: 'Steady learner' },
                    { student_id: 'advanced_student', display_name: 'Priya (Advanced)', difficulty: 'hard', xp: 2200, level: 22, description: 'Top performer' },
                ]);
            } finally {
                setIsLoading(false);
            }
        };
        fetchStudents();
    }, []);

    const handleSelect = (student: DemoStudent) => {
        setSelectedId(student.student_id);
        setTimeout(() => {
            login({
                id: student.student_id,
                name: student.display_name,
                xp: student.xp,
                level: student.level,
                current_difficulty: student.difficulty as 'easy' | 'medium' | 'hard',
            });
            navigate('/subjects');
        }, 300);
    };

    return (
        <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 px-4">
            {/* Background orbs */}
            <div className="pointer-events-none absolute inset-0 overflow-hidden">
                <div className="absolute -top-24 -right-24 h-72 w-72 rounded-full bg-blue-500/8 blur-3xl animate-orb" />
                <div className="absolute bottom-0 left-0 h-60 w-60 rounded-full bg-indigo-500/8 blur-3xl animate-orb" style={{ animationDelay: '3s' }} />
            </div>

            <div className="relative z-10 w-full max-w-lg animate-slide-up">
                <div className="glass-white rounded-3xl p-8 shadow-2xl">
                    <div className="text-center mb-8">
                        <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-lg shadow-blue-500/25">
                            <Zap className="h-7 w-7 text-white" />
                        </div>
                        <h1 className="text-2xl font-black text-slate-800 mb-1">Choose Your Profile</h1>
                        <p className="text-sm text-slate-500">Each profile adapts AI difficulty to match learning level</p>
                    </div>

                    {error && (
                        <div className="mb-4 rounded-xl bg-amber-50 border border-amber-200 px-4 py-2.5 text-sm text-amber-700 animate-slide-up">
                            {error}
                        </div>
                    )}

                    {isLoading ? (
                        <div className="space-y-4">
                            {[1, 2, 3].map(i => (
                                <div key={i} className="h-24 animate-pulse rounded-2xl bg-slate-100" />
                            ))}
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {students.map((student, idx) => {
                                const config = DIFFICULTY_CONFIG[student.difficulty] || DIFFICULTY_CONFIG.medium;
                                const isSelected = selectedId === student.student_id;

                                return (
                                    <button
                                        key={student.student_id}
                                        onClick={() => handleSelect(student)}
                                        className={`animate-slide-up stagger-${idx + 1} group flex w-full items-center gap-4 rounded-2xl border-2 p-4 text-left transition-all duration-300 ${isSelected
                                                ? `border-blue-500 bg-blue-50 scale-[0.97] ring-4 ${config.ring}`
                                                : 'border-slate-200/70 bg-white hover:border-blue-200 hover:shadow-lg hover:scale-[1.02]'
                                            }`}
                                    >
                                        {/* Avatar */}
                                        <div className={`relative flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br ${config.gradient} shadow-lg text-2xl transition-transform group-hover:scale-110`}>
                                            {AVATARS[idx % AVATARS.length]}
                                            <div className="absolute -bottom-1 -right-1 flex h-5 w-5 items-center justify-center rounded-full bg-white shadow-sm text-[10px] font-black text-slate-700">
                                                {student.level}
                                            </div>
                                        </div>

                                        {/* Info */}
                                        <div className="flex-1 min-w-0">
                                            <p className="font-bold text-slate-800 truncate">{student.display_name}</p>
                                            <p className="text-xs text-slate-500 mt-0.5">{student.description}</p>
                                            <div className="flex items-center gap-2 mt-2">
                                                <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider ${config.badge}`}>
                                                    {student.difficulty}
                                                </span>
                                                <span className="flex items-center gap-1 text-xs text-slate-400">
                                                    <Star className="h-3 w-3 text-amber-400 fill-amber-400" />
                                                    {student.xp} XP
                                                </span>
                                            </div>
                                        </div>

                                        {/* Arrow */}
                                        <TrendingUp className={`h-5 w-5 shrink-0 transition-all ${isSelected ? 'text-blue-500 rotate-12' : 'text-slate-300 group-hover:text-blue-400 group-hover:translate-x-1'}`} />
                                    </button>
                                );
                            })}
                        </div>
                    )}

                    <p className="mt-6 text-center text-xs text-slate-400">
                        CBSE Class 10 • Offline AI • Adaptive Learning Engine
                    </p>
                </div>
            </div>
        </div>
    );
}
