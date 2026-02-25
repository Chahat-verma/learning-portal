import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Calculator, Beaker, GraduationCap, ChevronRight, BookOpen } from 'lucide-react';
import { contentService } from '@/services/content';
import type { Subject } from '@/types';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';

const ICONS: Record<string, any> = {
    Calculator,
    Beaker,
    Book: BookOpen,
};

const SUBJECT_STYLES: Record<string, { gradient: string; glow: string; icon: string }> = {
    blue: { gradient: 'from-blue-500 to-indigo-600', glow: 'shadow-blue-500/25', icon: 'bg-blue-400/20 text-white' },
    green: { gradient: 'from-emerald-500 to-teal-600', glow: 'shadow-emerald-500/25', icon: 'bg-emerald-400/20 text-white' },
    purple: { gradient: 'from-violet-500 to-purple-600', glow: 'shadow-violet-500/25', icon: 'bg-violet-400/20 text-white' },
};

export function SubjectSelectPage() {
    const navigate = useNavigate();
    const [subjects, setSubjects] = useState<Subject[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchSubjects = async () => {
            try {
                const data = await contentService.getSubjects();
                setSubjects(data);
            } catch (error) {
                console.error("Failed to fetch subjects", error);
            } finally {
                setLoading(false);
            }
        };
        fetchSubjects();
    }, []);

    if (loading) {
        return (
            <div className="p-6">
                <h1 className="mb-6 text-2xl font-bold text-slate-800">Select a Subject</h1>
                <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                    {[1, 2].map(i => <LoadingSkeleton key={i} className="h-56 w-full rounded-3xl" />)}
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            <header className="animate-slide-up">
                <h1 className="text-3xl font-black text-slate-900">
                    What do you want to <span className="gradient-text">learn</span> today?
                </h1>
                <p className="mt-2 text-slate-500">Select a subject to start your personalized session.</p>
            </header>

            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                {subjects.map((subject, idx) => {
                    const Icon = ICONS[subject.icon] || GraduationCap;
                    const style = SUBJECT_STYLES[subject.color] || SUBJECT_STYLES.blue;

                    return (
                        <button
                            key={subject.id}
                            onClick={() => navigate(`/subjects/${subject.id}/chapters`)}
                            className={`animate-slide-up stagger-${idx + 1} group relative flex h-56 flex-col justify-between overflow-hidden rounded-3xl bg-gradient-to-br ${style.gradient} p-8 text-left shadow-xl ${style.glow} transition-all hover:scale-[1.03] hover:shadow-2xl active:scale-[0.98]`}
                        >
                            {/* Background decoration */}
                            <div className="absolute -right-12 -top-12 h-48 w-48 rounded-full bg-white/5 transition-transform group-hover:scale-150" />
                            <div className="absolute right-8 bottom-8 h-24 w-24 rounded-full bg-white/5" />

                            {/* Icon */}
                            <div className={`flex h-16 w-16 items-center justify-center rounded-2xl ${style.icon} backdrop-blur-sm transition-transform group-hover:scale-110 group-hover:rotate-3`}>
                                <Icon className="h-8 w-8" />
                            </div>

                            {/* Content */}
                            <div className="relative z-10">
                                <h3 className="text-2xl font-black text-white tracking-tight">
                                    {subject.name}
                                </h3>
                                <div className="mt-2 flex items-center gap-2">
                                    <span className="rounded-full bg-white/20 px-3 py-1 text-xs font-semibold text-white/90 backdrop-blur-sm">
                                        Interactive Learning
                                    </span>
                                    <ChevronRight className="h-4 w-4 text-white/60 transition-transform group-hover:translate-x-1" />
                                </div>
                            </div>
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
