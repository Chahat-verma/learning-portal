import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Trophy, ArrowRight, Zap, BookOpen } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import api from '../services/api';
import clsx from 'clsx';

interface QuizQuestion {
    id: number;
    question: string;
    options: string[];
}

interface QuizData {
    quiz_id: string;
    difficulty: string;
    questions: QuizQuestion[];
}

interface QuizResult {
    score: number;
    total: number;
    xp_gained: number;
    difficulty: string;
    confidence_score: number;
    learning_momentum: number;
    weak_topics: string[];
}

interface SubjectOption {
    id: string;
    name: string;
    chapters: Array<{ id: string; name: string; description?: string }>;
}

export function QuizPage() {
    const { student } = useAuthStore();
    const navigate = useNavigate();
    const [searchParams] = useSearchParams();

    const [step, setStep] = useState<'setup' | 'quiz' | 'result'>('setup');
    const [subject, setSubject] = useState(searchParams.get('subject') || '');
    const [chapterId, setChapterId] = useState(searchParams.get('chapter') || '');
    const [quiz, setQuiz] = useState<QuizData | null>(null);
    const [answers, setAnswers] = useState<Record<number, string>>({});
    const [currentQ, setCurrentQ] = useState(0);
    const [result, setResult] = useState<QuizResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [startTime] = useState(Date.now());

    // Dynamically fetch subjects and chapters from API
    const [subjectOptions, setSubjectOptions] = useState<SubjectOption[]>([]);
    const [chaptersLoading, setChaptersLoading] = useState(true);

    useEffect(() => {
        const fetchSubjects = async () => {
            try {
                const res = await api.get('/subjects');
                const subjects = res.data;
                const withChapters = await Promise.all(
                    subjects.map(async (s: any) => {
                        const chRes = await api.get(`/subjects/${s.id}/chapters`);
                        return { ...s, chapters: chRes.data };
                    })
                );
                setSubjectOptions(withChapters);
            } catch (err) {
                console.error('Failed to fetch subjects:', err);
            } finally {
                setChaptersLoading(false);
            }
        };
        fetchSubjects();
    }, []);

    const selectedSubject = subjectOptions.find(s => s.id === subject);

    const handleStartQuiz = async () => {
        if (!subject || !chapterId) return;
        setLoading(true);
        setError(null);
        try {
            const res = await api.post('/quiz/generate', {
                student_id: student?.id,
                subject,
                chapter_id: chapterId,
                num_questions: 5,
            });
            if (!res.data?.questions?.length) {
                setError('Quiz returned no questions. Please try again.');
                return;
            }
            setQuiz(res.data);
            setStep('quiz');
            setCurrentQ(0);
            setAnswers({});
        } catch (err: any) {
            console.error('Quiz generation failed:', err);
            setError(err?.message?.includes('timeout') ? 'Server timed out. Try again.' : 'Failed to generate quiz. Check your connection.');
        } finally {
            setLoading(false);
        }
    };

    const handleSelectAnswer = (questionId: number, answer: string) => {
        setAnswers(prev => ({ ...prev, [questionId]: answer }));
    };

    const handleSubmitQuiz = async () => {
        if (!quiz) return;
        setLoading(true);
        setError(null);
        const timeTaken = (Date.now() - startTime) / 1000;
        try {
            const res = await api.post('/quiz/submit', {
                student_id: student?.id,
                quiz_id: quiz.quiz_id,
                answers,
                time_taken: timeTaken,
            });
            setResult(res.data);
            setStep('result');
        } catch (err: any) {
            console.error('Quiz submit failed:', err);
            setError('Failed to submit quiz. Your answers were not saved.');
        } finally {
            setLoading(false);
        }
    };

    // SETUP
    if (step === 'setup') {
        return (
            <div className="max-w-2xl mx-auto space-y-6">
                {error && (
                    <div className="rounded-xl bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                        ⚠️ {error}
                    </div>
                )}
                <div className="text-center mb-8">
                    <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 shadow-lg mb-4">
                        <Trophy className="h-8 w-8 text-white" />
                    </div>
                    <h1 className="text-2xl font-bold text-slate-800">Quiz Mode</h1>
                    <p className="text-slate-500 mt-1">Test your knowledge and earn XP</p>
                </div>

                {/* Subject Selection */}
                <div>
                    <label className="block text-sm font-semibold text-slate-700 mb-2">Select Subject</label>
                    <div className="grid grid-cols-2 gap-3">
                        {subjectOptions.map(s => (
                            <button
                                key={s.id}
                                onClick={() => { setSubject(s.id); setChapterId(''); }}
                                className={clsx(
                                    'rounded-xl border-2 p-4 text-left transition-all',
                                    subject === s.id
                                        ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                                        : 'border-slate-200 bg-white hover:border-slate-300'
                                )}
                            >
                                <p className="font-semibold text-slate-800">{s.name}</p>
                                <p className="text-xs text-slate-500 mt-0.5">{s.chapters.length} chapters</p>
                            </button>
                        ))}
                    </div>
                </div>

                {/* Chapter Selection */}
                {selectedSubject && (
                    <div>
                        <label className="block text-sm font-semibold text-slate-700 mb-2">Select Chapter</label>
                        <div className="space-y-2">
                            {selectedSubject.chapters.map(ch => (
                                <button
                                    key={ch.id}
                                    onClick={() => setChapterId(ch.id)}
                                    className={clsx(
                                        'w-full flex items-center gap-3 rounded-xl border-2 p-3 text-left transition-all',
                                        chapterId === ch.id
                                            ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                                            : 'border-slate-200 bg-white hover:border-slate-300'
                                    )}
                                >
                                    <BookOpen className="h-4 w-4 text-slate-400 shrink-0" />
                                    <span className="text-sm font-medium text-slate-700">{ch.name}</span>
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                <button
                    onClick={handleStartQuiz}
                    disabled={!subject || !chapterId || loading}
                    className={clsx(
                        'w-full rounded-xl py-3.5 text-sm font-semibold transition-all',
                        subject && chapterId && !loading
                            ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg hover:shadow-xl active:scale-[0.98]'
                            : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                    )}
                >
                    {loading ? (
                        <span className="flex items-center justify-center gap-2">
                            <div className="h-4 w-4 rounded-full border-2 border-white border-t-transparent animate-spin" />
                            Generating Quiz...
                        </span>
                    ) : 'Start Quiz (5 Questions)'}
                </button>
            </div>
        );
    }

    // QUIZ
    if (step === 'quiz' && quiz) {
        const q = quiz.questions[currentQ];
        const isLast = currentQ === quiz.questions.length - 1;
        const allAnswered = quiz.questions.every(q => answers[q.id]);

        return (
            <div className="max-w-2xl mx-auto space-y-6">
                {/* Progress */}
                <div className="flex items-center gap-3">
                    <div className="flex-1 h-2 rounded-full bg-slate-200 overflow-hidden">
                        <div
                            className="h-full rounded-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-500"
                            style={{ width: `${((currentQ + 1) / quiz.questions.length) * 100}%` }}
                        />
                    </div>
                    <span className="text-xs font-semibold text-slate-500">
                        {currentQ + 1}/{quiz.questions.length}
                    </span>
                </div>

                {/* Difficulty Badge */}
                <div className="flex items-center gap-2">
                    <span className={clsx(
                        'rounded-full px-3 py-0.5 text-xs font-semibold',
                        quiz.difficulty === 'easy' ? 'bg-emerald-100 text-emerald-700' :
                            quiz.difficulty === 'hard' ? 'bg-red-100 text-red-700' :
                                'bg-amber-100 text-amber-700'
                    )}>
                        {quiz.difficulty.toUpperCase()}
                    </span>
                </div>

                {/* Question */}
                <div className="rounded-2xl bg-white border border-slate-200 p-6 shadow-sm">
                    <p className="text-lg font-semibold text-slate-800 leading-relaxed">{q.question}</p>
                </div>

                {/* Options */}
                <div className="space-y-3">
                    {q.options.map((option, idx) => (
                        <button
                            key={idx}
                            onClick={() => handleSelectAnswer(q.id, option)}
                            className={clsx(
                                'w-full flex items-center gap-3 rounded-xl border-2 p-4 text-left transition-all',
                                answers[q.id] === option
                                    ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
                                    : 'border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50'
                            )}
                        >
                            <div className={clsx(
                                'flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-sm font-bold',
                                answers[q.id] === option
                                    ? 'bg-blue-600 text-white'
                                    : 'bg-slate-100 text-slate-500'
                            )}>
                                {String.fromCharCode(65 + idx)}
                            </div>
                            <span className="text-sm font-medium text-slate-700">{option}</span>
                        </button>
                    ))}
                </div>

                {/* Navigation */}
                <div className="flex gap-3">
                    {currentQ > 0 && (
                        <button
                            onClick={() => setCurrentQ(prev => prev - 1)}
                            className="flex-1 rounded-xl border border-slate-200 py-3 text-sm font-semibold text-slate-600 hover:bg-slate-50"
                        >
                            Previous
                        </button>
                    )}
                    {isLast ? (
                        <button
                            onClick={handleSubmitQuiz}
                            disabled={!allAnswered || loading}
                            className={clsx(
                                'flex-1 rounded-xl py-3 text-sm font-semibold transition-all',
                                allAnswered && !loading
                                    ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg active:scale-[0.98]'
                                    : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                            )}
                        >
                            {loading ? 'Submitting...' : 'Submit Quiz'}
                        </button>
                    ) : (
                        <button
                            onClick={() => setCurrentQ(prev => prev + 1)}
                            disabled={!answers[q.id]}
                            className={clsx(
                                'flex-1 flex items-center justify-center gap-2 rounded-xl py-3 text-sm font-semibold transition-all',
                                answers[q.id]
                                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                                    : 'bg-slate-200 text-slate-400 cursor-not-allowed'
                            )}
                        >
                            Next <ArrowRight className="h-4 w-4" />
                        </button>
                    )}
                </div>
            </div>
        );
    }

    // RESULT
    if (step === 'result' && result) {
        const percentage = Math.round((result.score / result.total) * 100);
        const isGood = percentage >= 60;

        return (
            <div className="max-w-xl mx-auto text-center space-y-6">
                <div className={clsx(
                    'rounded-2xl p-8 shadow-xl',
                    isGood
                        ? 'bg-gradient-to-br from-emerald-500 to-teal-600'
                        : 'bg-gradient-to-br from-amber-500 to-orange-600'
                )}>
                    <div className="text-6xl mb-3">{isGood ? '🎉' : '💪'}</div>
                    <h2 className="text-2xl font-bold text-white">
                        {isGood ? 'Great Job!' : 'Keep Practicing!'}
                    </h2>
                    <p className="text-5xl font-black text-white mt-4">
                        {result.score}/{result.total}
                    </p>
                    <p className="text-white/80 text-sm mt-1">{percentage}% Accuracy</p>
                </div>

                <div className="grid grid-cols-3 gap-3">
                    <div className="rounded-xl bg-amber-50 border border-amber-200 p-4">
                        <Zap className="h-5 w-5 text-amber-500 mx-auto mb-1" />
                        <p className="text-xl font-bold text-slate-800">+{result.xp_gained}</p>
                        <p className="text-[10px] text-slate-500">XP Earned</p>
                    </div>
                    <div className="rounded-xl bg-purple-50 border border-purple-200 p-4">
                        <p className="text-xl font-bold text-slate-800">{Math.round(result.confidence_score * 100)}%</p>
                        <p className="text-[10px] text-slate-500">Confidence</p>
                    </div>
                    <div className="rounded-xl bg-blue-50 border border-blue-200 p-4">
                        <p className="text-xl font-bold text-slate-800 uppercase">{result.difficulty}</p>
                        <p className="text-[10px] text-slate-500">Next Level</p>
                    </div>
                </div>

                <div className="flex gap-3">
                    <button
                        onClick={() => { setStep('setup'); setQuiz(null); setResult(null); }}
                        className="flex-1 rounded-xl border border-slate-200 py-3 text-sm font-semibold text-slate-600 hover:bg-slate-50"
                    >
                        New Quiz
                    </button>
                    <button
                        onClick={() => navigate('/dashboard')}
                        className="flex-1 rounded-xl bg-blue-600 py-3 text-sm font-semibold text-white hover:bg-blue-700"
                    >
                        Dashboard
                    </button>
                </div>
            </div>
        );
    }

    return null;
}
