import { useState, useEffect, memo } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, Zap, Trophy, PlayCircle, Brain, TrendingUp, Target, ChevronRight, Activity, Sparkles } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import api from '../services/api';

interface StudentStats {
    xp: number;
    level: number;
    difficulty: string;
    confidence: number;
    momentum: number;
    total_questions: number;
    correct_answers: number;
    accuracy: number;
    videos_watched: number;
}

interface ChapterProgress {
    subject: string;
    subject_name: string;
    chapter_id: string;
    chapter_name: string;
    questions_asked: number;
    quiz_attempts: number;
    avg_quiz_score: number;
}

// Loading skeleton — lightweight
function Skeleton({ className }: { className?: string }) {
    return <div className={`animate-pulse rounded-xl bg-slate-200 ${className || ''}`} />;
}

// Stat card — memoized
const StatCard = memo(({ label, value, icon: Icon, color, bg }: {
    label: string; value: string | number; icon: any; color: string; bg: string;
}) => (
    <div className={`rounded-2xl ${bg} border border-slate-200 p-5 transition-shadow hover:shadow-md`}>
        <Icon className={`h-5 w-5 ${color} mb-3`} />
        <p className="text-2xl font-black text-slate-800">{value}</p>
        <p className="text-xs text-slate-500 mt-1 font-medium">{label}</p>
    </div>
));

// Quick action card — memoized
const ActionCard = memo(({ title, desc, icon: Icon, gradient, shadow, onClick }: {
    title: string; desc: string; icon: any; gradient: string; shadow: string; onClick: () => void;
}) => (
    <button onClick={onClick}
        className="group flex items-center gap-4 rounded-2xl bg-white border border-slate-200 p-5 text-left transition-shadow hover:shadow-md w-full">
        <div className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br ${gradient} shadow-lg ${shadow}`}>
            <Icon className="h-7 w-7 text-white" />
        </div>
        <div className="flex-1 min-w-0">
            <p className="font-bold text-slate-800">{title}</p>
            <p className="text-xs text-slate-500 mt-0.5">{desc}</p>
        </div>
        <ChevronRight className="h-5 w-5 text-slate-300 group-hover:text-slate-500 transition-colors" />
    </button>
));

export function DashboardPage() {
    const { student } = useAuthStore();
    const navigate = useNavigate();
    const [stats, setStats] = useState<StudentStats | null>(null);
    const [systemHealth, setSystemHealth] = useState<any>(null);
    const [chapterProgress, setChapterProgress] = useState<ChapterProgress[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!student) return;
        const controller = new AbortController();
        const fetchData = async () => {
            try {
                const [statsRes, healthRes, progressRes] = await Promise.all([
                    api.get(`/student/${student.id}/stats`),
                    api.get('/health'),
                    api.get(`/student/${student.id}/chapter-progress`),
                ]);
                setStats(statsRes.data);
                setSystemHealth(healthRes.data);
                setChapterProgress(progressRes.data || []);
            } catch (err: any) {
                console.error('Dashboard fetch error:', err);
                setError(err?.message?.includes('timeout') ? 'Server took too long. Try refreshing.' : 'Could not load dashboard data.');
            } finally {
                setLoading(false);
            }
        };
        fetchData();
        return () => controller.abort();
    }, [student]);

    if (loading) {
        return (
            <div className="space-y-6 p-6">
                <Skeleton className="h-44 w-full rounded-3xl" />
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-28" />)}
                </div>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {[1, 2, 3].map(i => <Skeleton key={i} className="h-24" />)}
                </div>
            </div>
        );
    }

    const accuracy = stats?.accuracy || 0;

    return (
        <div className="space-y-6">
            {/* Error banner */}
            {error && (
                <div className="rounded-xl bg-amber-50 border border-amber-200 px-4 py-3 text-sm text-amber-700">
                    ⚠️ {error}
                </div>
            )}

            {/* Hero Card — lightweight gradient, no blur */}
            <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-blue-600 via-indigo-600 to-violet-700 p-7 md:p-10 text-white shadow-xl">
                <div className="absolute -right-16 -top-16 h-56 w-56 rounded-full bg-white/5" />
                <div className="relative z-10">
                    <div className="flex items-center gap-2 mb-1">
                        <Sparkles className="h-4 w-4 text-blue-300" />
                        <p className="text-blue-200 text-sm font-medium">Welcome back,</p>
                    </div>
                    <h1 className="text-3xl md:text-4xl font-black mt-1">{student?.name}</h1>
                    <p className="text-blue-200 mt-1 text-sm">
                        Level {stats?.level || 1} • <span className="uppercase font-semibold">{stats?.difficulty || 'MEDIUM'}</span> difficulty
                    </p>
                    <div className="mt-6 flex items-center gap-8">
                        <div>
                            <p className="text-4xl font-black">{stats?.xp || 0}</p>
                            <p className="text-xs text-blue-300 font-medium">Total XP</p>
                        </div>
                        <div className="h-12 w-px bg-white/20" />
                        <div>
                            <p className="text-4xl font-black">{accuracy}%</p>
                            <p className="text-xs text-blue-300 font-medium">Accuracy</p>
                        </div>
                        <div className="h-12 w-px bg-white/20" />
                        <div>
                            <p className="text-4xl font-black">{stats?.videos_watched || 0}</p>
                            <p className="text-xs text-blue-300 font-medium">Videos</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <StatCard label="XP Earned" value={stats?.xp || 0} icon={Zap} color="text-amber-500" bg="bg-amber-50" />
                <StatCard label="Confidence" value={`${Math.round((stats?.confidence || 0) * 100)}%`} icon={Brain} color="text-purple-500" bg="bg-purple-50" />
                <StatCard label="Momentum" value={(stats?.momentum || 0).toFixed(1)} icon={TrendingUp} color="text-emerald-500" bg="bg-emerald-50" />
                <StatCard label="Questions" value={stats?.total_questions || 0} icon={Target} color="text-blue-500" bg="bg-blue-50" />
            </div>

            {/* Quick Actions */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <ActionCard title="Continue Learning" desc="Pick up where you left off" icon={BookOpen} gradient="from-blue-500 to-indigo-600" shadow="shadow-blue-500/20" onClick={() => navigate('/subjects')} />
                <ActionCard title="Take a Quiz" desc="Test your knowledge" icon={Trophy} gradient="from-violet-500 to-purple-600" shadow="shadow-violet-500/20" onClick={() => navigate('/quiz')} />
                <ActionCard title="Watch Videos" desc="NCERT video lessons" icon={PlayCircle} gradient="from-emerald-500 to-teal-600" shadow="shadow-emerald-500/20" onClick={() => navigate('/videos')} />
            </div>

            {/* Chapter Progress */}
            {chapterProgress.length > 0 && (
                <div className="rounded-2xl bg-white border border-slate-200 p-6">
                    <h3 className="text-sm font-bold text-slate-700 mb-4 flex items-center gap-2">
                        <BookOpen className="h-4 w-4 text-blue-500" /> Chapter Progress
                    </h3>
                    <div className="space-y-2">
                        {chapterProgress.map(ch => (
                            <div key={`${ch.subject}-${ch.chapter_id}`}
                                className="flex flex-col sm:flex-row sm:items-center justify-between rounded-xl px-4 py-3 border border-slate-100 bg-slate-50/50 hover:bg-slate-50">
                                <div className="min-w-0 mb-1 sm:mb-0">
                                    <p className="text-sm font-semibold text-slate-800 truncate">{ch.chapter_name}</p>
                                    <p className="text-[11px] text-slate-400">{ch.subject_name}</p>
                                </div>
                                <div className="flex items-center gap-5 shrink-0">
                                    <div className="text-center"><p className="text-sm font-black text-slate-700">{ch.questions_asked}</p><p className="text-[10px] text-slate-400">Chats</p></div>
                                    <div className="text-center"><p className="text-sm font-black text-slate-700">{ch.quiz_attempts}</p><p className="text-[10px] text-slate-400">Quizzes</p></div>
                                    <div className="text-center">
                                        <p className={`text-sm font-black ${ch.avg_quiz_score >= 70 ? 'text-emerald-600' : ch.avg_quiz_score >= 40 ? 'text-amber-600' : ch.avg_quiz_score > 0 ? 'text-red-500' : 'text-slate-300'}`}>
                                            {ch.avg_quiz_score > 0 ? `${ch.avg_quiz_score}%` : '—'}
                                        </p>
                                        <p className="text-[10px] text-slate-400">Score</p>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* System Status */}
            {systemHealth && (
                <div className="rounded-2xl bg-slate-900 p-6 text-white">
                    <h3 className="text-sm font-bold text-slate-300 mb-4 flex items-center gap-2">
                        <Activity className="h-4 w-4 text-emerald-400" /> System Status
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {[
                            { label: 'Ollama Brain', active: systemHealth.ollama_active },
                            { label: 'RAG Index', active: systemHealth.rag_index_loaded },
                            { label: 'ChromaDB', active: systemHealth.chroma_available },
                            { label: `${systemHealth.rag_lessons || 0} Lessons`, active: true },
                        ].map(s => (
                            <div key={s.label} className="flex items-center gap-2.5 rounded-xl bg-white/5 border border-white/10 px-4 py-3">
                                <div className={`h-2.5 w-2.5 rounded-full ${s.active ? 'bg-emerald-400' : 'bg-red-400'}`} />
                                <span className="text-xs font-semibold text-slate-300">{s.label}</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}
