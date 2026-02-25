import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlayCircle, CheckCircle, Clock, BookOpen, Zap, ArrowLeft, Search } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import api from '../services/api';

interface Video {
    id: string;
    title: string;
    duration: string;
    thumbnail: string;
    description: string;
    subject: string;
    chapter_id: string;
    watched: boolean;
}

export function VideoLibraryPage() {
    const { student } = useAuthStore();
    const navigate = useNavigate();
    const [videos, setVideos] = useState<Video[]>([]);
    const [loading, setLoading] = useState(true);
    const [selectedSubject, setSelectedSubject] = useState<string>('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [watchingId, setWatchingId] = useState<string | null>(null);

    useEffect(() => {
        fetchVideos();
    }, [student]);

    const fetchVideos = async () => {
        try {
            const res = await api.get('/videos', {
                params: { student_id: student?.id }
            });
            setVideos(res.data);
        } catch (err) {
            console.error('Failed to fetch videos:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleWatch = async (videoId: string) => {
        setWatchingId(videoId);

        // Simulate watching delay
        setTimeout(async () => {
            try {
                await api.post(`/videos/${videoId}/watch`, null, {
                    params: { student_id: student?.id }
                });
                // Update local state
                setVideos(prev => prev.map(v =>
                    v.id === videoId ? { ...v, watched: true } : v
                ));
            } catch (err) {
                console.error('Watch error:', err);
            } finally {
                setWatchingId(null);
            }
        }, 1500);
    };

    const subjects = ['all', ...new Set(videos.map(v => v.subject))];
    const filtered = videos
        .filter(v => selectedSubject === 'all' || v.subject === selectedSubject)
        .filter(v => !searchQuery || v.title.toLowerCase().includes(searchQuery.toLowerCase()) || v.description.toLowerCase().includes(searchQuery.toLowerCase()));

    const watchedCount = videos.filter(v => v.watched).length;
    const totalXpFromVideos = watchedCount * 50;

    if (loading) {
        return (
            <div className="animate-pulse space-y-6 p-4">
                <div className="h-32 rounded-2xl bg-slate-200" />
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {[1, 2, 3, 4].map(i => <div key={i} className="h-36 rounded-xl bg-slate-200" />)}
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="relative overflow-hidden rounded-2xl bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-700 p-6 md:p-8 text-white shadow-xl">
                <div className="absolute -right-8 -top-8 h-40 w-40 rounded-full bg-white/5" />
                <div className="relative z-10">
                    <div className="flex items-center gap-3 mb-3">
                        <PlayCircle className="h-8 w-8" />
                        <div>
                            <h1 className="text-2xl md:text-3xl font-bold">Video Library</h1>
                            <p className="text-emerald-200 text-sm">Kolibri Integration • NCERT Aligned</p>
                        </div>
                    </div>
                    <div className="flex items-center gap-6 mt-4">
                        <div>
                            <p className="text-2xl font-bold">{videos.length}</p>
                            <p className="text-xs text-emerald-300">Total Videos</p>
                        </div>
                        <div className="h-8 w-px bg-white/20" />
                        <div>
                            <p className="text-2xl font-bold">{watchedCount}</p>
                            <p className="text-xs text-emerald-300">Watched</p>
                        </div>
                        <div className="h-8 w-px bg-white/20" />
                        <div>
                            <p className="text-2xl font-bold">{totalXpFromVideos}</p>
                            <p className="text-xs text-emerald-300">XP Earned</p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Filters */}
            <div className="flex flex-col sm:flex-row gap-3">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <input
                        type="text"
                        placeholder="Search videos..."
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                        className="w-full rounded-xl border border-slate-200 bg-white pl-10 pr-4 py-2.5 text-sm text-slate-700 placeholder-slate-400 focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
                    />
                </div>
                <div className="flex gap-2 overflow-x-auto">
                    {subjects.map(subj => (
                        <button
                            key={subj}
                            onClick={() => setSelectedSubject(subj)}
                            className={`shrink-0 rounded-full px-4 py-2 text-xs font-semibold transition-all ${selectedSubject === subj
                                    ? 'bg-blue-600 text-white shadow-md'
                                    : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
                                }`}
                        >
                            {subj === 'all' ? 'All Subjects' : subj.charAt(0).toUpperCase() + subj.slice(1)}
                        </button>
                    ))}
                </div>
            </div>

            {/* Video Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filtered.map((video) => (
                    <div
                        key={video.id}
                        className={`group rounded-xl border bg-white overflow-hidden transition-all hover:shadow-lg ${video.watched ? 'border-emerald-200' : 'border-slate-200 hover:border-blue-200'
                            }`}
                    >
                        {/* Thumbnail area */}
                        <div className={`relative flex items-center justify-center h-32 ${video.watched
                                ? 'bg-gradient-to-br from-emerald-50 to-teal-50'
                                : 'bg-gradient-to-br from-slate-50 to-blue-50'
                            }`}>
                            <span className="text-4xl">{video.thumbnail}</span>
                            {video.watched && (
                                <div className="absolute top-3 right-3 flex items-center gap-1 rounded-full bg-emerald-500 px-2 py-0.5">
                                    <CheckCircle className="h-3 w-3 text-white" />
                                    <span className="text-[10px] font-semibold text-white">Watched</span>
                                </div>
                            )}
                            {watchingId === video.id && (
                                <div className="absolute inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm">
                                    <div className="flex flex-col items-center gap-2">
                                        <div className="h-8 w-8 rounded-full border-2 border-white border-t-transparent animate-spin" />
                                        <span className="text-white text-xs font-medium">Watching...</span>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Info */}
                        <div className="p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <span className="rounded-full bg-blue-50 border border-blue-100 px-2 py-0.5 text-[10px] font-semibold text-blue-600 uppercase">
                                    {video.subject}
                                </span>
                                <span className="flex items-center gap-1 text-[10px] text-slate-400">
                                    <Clock className="h-2.5 w-2.5" />
                                    {video.duration}
                                </span>
                            </div>
                            <h3 className="font-semibold text-slate-800 text-sm leading-tight mb-1">{video.title}</h3>
                            <p className="text-xs text-slate-500 line-clamp-2 mb-3">{video.description}</p>

                            <button
                                onClick={() => !video.watched && handleWatch(video.id)}
                                disabled={video.watched || watchingId === video.id}
                                className={`w-full flex items-center justify-center gap-2 rounded-lg py-2 text-xs font-semibold transition-all ${video.watched
                                        ? 'bg-emerald-50 text-emerald-600 border border-emerald-200 cursor-default'
                                        : 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm active:scale-95'
                                    }`}
                            >
                                {video.watched ? (
                                    <>
                                        <CheckCircle className="h-3.5 w-3.5" />
                                        Completed • +50 XP
                                    </>
                                ) : (
                                    <>
                                        <PlayCircle className="h-3.5 w-3.5" />
                                        Watch Now • Earn 50 XP
                                    </>
                                )}
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            {filtered.length === 0 && (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                    <BookOpen className="h-12 w-12 text-slate-300 mb-3" />
                    <p className="text-slate-500 font-medium">No videos found</p>
                    <p className="text-sm text-slate-400">Try a different search or filter</p>
                </div>
            )}
        </div>
    );
}
