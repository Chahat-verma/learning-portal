import { useNavigate } from 'react-router-dom';
import { Zap, Wifi, BookOpen, Brain, Shield, Sparkles } from 'lucide-react';

export function LandingPage() {
    const navigate = useNavigate();

    const features = [
        { icon: Wifi, label: '100% Offline', desc: 'Works without internet', color: 'from-emerald-400 to-teal-500' },
        { icon: Shield, label: 'NCERT Locked', desc: 'Zero hallucination RAG', color: 'from-blue-400 to-indigo-500' },
        { icon: Brain, label: 'AI Adaptive', desc: 'Personalized difficulty', color: 'from-violet-400 to-purple-500' },
    ];

    return (
        <div className="relative flex min-h-screen flex-col items-center justify-center overflow-hidden bg-gradient-to-br from-slate-900 via-blue-950 to-slate-900 px-4 text-white">
            {/* Animated background orbs */}
            <div className="pointer-events-none absolute inset-0 overflow-hidden">
                <div className="absolute -top-32 -left-32 h-96 w-96 rounded-full bg-blue-500/10 blur-3xl animate-orb" />
                <div className="absolute top-1/2 -right-48 h-[500px] w-[500px] rounded-full bg-indigo-500/10 blur-3xl animate-orb" style={{ animationDelay: '2s' }} />
                <div className="absolute -bottom-24 left-1/3 h-80 w-80 rounded-full bg-cyan-500/10 blur-3xl animate-orb" style={{ animationDelay: '4s' }} />
                {/* Grid overlay */}
                <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(circle, white 1px, transparent 1px)', backgroundSize: '40px 40px' }} />
            </div>

            <div className="relative z-10 text-center max-w-2xl">
                {/* Logo */}
                <div className="animate-slide-up mx-auto mb-8 flex h-24 w-24 items-center justify-center rounded-3xl bg-gradient-to-br from-blue-500 to-indigo-600 shadow-2xl shadow-blue-500/30 animate-glow">
                    <Zap className="h-12 w-12 text-white drop-shadow-lg" />
                </div>

                {/* Title */}
                <h1 className="animate-slide-up stagger-1 mb-3 text-6xl font-black tracking-tight">
                    <span className="gradient-text">ICAN</span>
                </h1>
                <p className="animate-slide-up stagger-2 mb-2 text-xl text-blue-200 font-semibold tracking-wide">
                    Intelligent Classroom AI Network
                </p>
                <p className="animate-slide-up stagger-3 mb-10 text-sm text-slate-400 leading-relaxed max-w-md mx-auto">
                    India's first offline AI tutor — NCERT-locked RAG pipeline with adaptive difficulty,
                    real-time progress tracking, and zero hallucination guarantee.
                </p>

                {/* CTA Button */}
                <div className="animate-slide-up stagger-4 mb-14">
                    <button
                        onClick={() => navigate('/login')}
                        className="group relative inline-flex items-center gap-2 rounded-2xl bg-gradient-to-r from-blue-500 via-blue-600 to-indigo-600 px-10 py-4 text-base font-bold text-white shadow-xl shadow-blue-500/25 transition-all hover:shadow-blue-500/40 hover:scale-105 active:scale-95 animate-gradient"
                    >
                        <Sparkles className="h-5 w-5 transition-transform group-hover:rotate-12" />
                        Start Learning
                        <div className="absolute inset-0 rounded-2xl animate-shimmer opacity-30" />
                    </button>
                </div>

                {/* Feature Cards */}
                <div className="grid grid-cols-3 gap-4 max-w-lg mx-auto">
                    {features.map((feat, i) => (
                        <div
                            key={feat.label}
                            className={`animate-slide-up stagger-${i + 3} glass rounded-2xl p-4 text-center transition-all hover:scale-105 hover:bg-white/10`}
                        >
                            <div className={`mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${feat.color} shadow-lg`}>
                                <feat.icon className="h-6 w-6 text-white" />
                            </div>
                            <p className="text-sm font-bold text-white">{feat.label}</p>
                            <p className="text-[11px] text-slate-400 mt-1">{feat.desc}</p>
                        </div>
                    ))}
                </div>

                {/* Bottom tagline */}
                <div className="animate-fade-in mt-16 flex items-center justify-center gap-3 text-xs text-slate-500">
                    <span className="flex items-center gap-1.5">
                        <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                        Ollama Active
                    </span>
                    <span className="h-3 w-px bg-slate-700" />
                    <span>CBSE Class 10</span>
                    <span className="h-3 w-px bg-slate-700" />
                    <span>Powered by Llama 3</span>
                </div>
            </div>
        </div>
    );
}
