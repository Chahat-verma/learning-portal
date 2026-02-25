import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { PlayCircle } from 'lucide-react';
import { contentService } from '@/services/content';
import type { Chapter } from '@/types';
import { LoadingSkeleton } from '@/components/LoadingSkeleton';

export function ChapterSelectPage() {
    const { subjectId } = useParams<{ subjectId: string }>();
    const navigate = useNavigate();
    const [chapters, setChapters] = useState<Chapter[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!subjectId) return;
        const fetchChapters = async () => {
            try {
                const data = await contentService.getChapters(subjectId);
                setChapters(data);
            } catch (error) {
                console.error("Failed to fetch chapters", error);
            } finally {
                setLoading(false);
            }
        };
        fetchChapters();
    }, [subjectId]);

    const handleSelectChapter = (chapterId: string) => {
        navigate(`/learn/${subjectId}/${chapterId}`);
    };

    if (loading) {
        return (
            <div className="p-6">
                <LoadingSkeleton className="mb-8 h-12 w-64" />
                <div className="space-y-4">
                    {[1, 2, 3, 4].map((i) => (
                        <LoadingSkeleton key={i} className="h-24 w-full rounded-xl" />
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-slate-50 p-4 md:p-8">
            <div className="mx-auto max-w-4xl">
                <button
                    onClick={() => navigate('/subjects')}
                    className="mb-6 flex items-center text-sm font-medium text-slate-500 hover:text-slate-800"
                >
                    ← Back to Subjects
                </button>

                <header className="mb-8">
                    <h1 className="text-3xl font-extrabold text-slate-900 capitalize">
                        {subjectId?.replace('_', ' ')} Modules
                    </h1>
                    <p className="mt-2 text-slate-600">Select a chapter to begin your lesson.</p>
                </header>

                <div className="grid gap-4">
                    {chapters.map((chapter, index) => (
                        <button
                            key={chapter.id}
                            onClick={() => handleSelectChapter(chapter.id)}
                            className="group flex w-full items-center justify-between rounded-2xl border border-slate-200 bg-white p-6 text-left shadow-sm transition-all hover:border-blue-200 hover:bg-blue-50/50 hover:shadow-md"
                        >
                            <div className="flex items-start gap-4">
                                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-600 font-bold">
                                    {index + 1}
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold text-slate-800 group-hover:text-blue-700">
                                        {chapter.name}
                                    </h3>
                                    <p className="text-sm text-slate-500">
                                        {chapter.description}
                                    </p>
                                </div>
                            </div>

                            <div className="flex items-center text-blue-600 opacity-0 transition-opacity group-hover:opacity-100">
                                <span className="mr-2 text-sm font-medium">Start</span>
                                <PlayCircle className="h-5 w-5" />
                            </div>
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}
