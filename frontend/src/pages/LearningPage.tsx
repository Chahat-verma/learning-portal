import { useState, useEffect, useRef, useCallback, memo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Send, ArrowLeft, Sparkles, Clock, BookOpen } from 'lucide-react';
import { ChatMessage } from '@/components/ChatMessage';
import { chatService } from '@/services/chat';
import { useAuthStore } from '@/store/useAuthStore';
import type { Message } from '@/types';
import clsx from 'clsx';

// Memoized chat message to prevent re-renders
const MemoizedChatMessage = memo(ChatMessage);

export function LearningPage() {
    const { subjectId, chapterId } = useParams<{ subjectId: string; chapterId: string }>();
    const navigate = useNavigate();
    const { student } = useAuthStore();

    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [sessionTime, setSessionTime] = useState(0);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);

    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, []);

    useEffect(() => { scrollToBottom(); }, [messages, scrollToBottom]);

    // Session timer
    useEffect(() => {
        const timer = setInterval(() => setSessionTime(t => t + 1), 1000);
        return () => clearInterval(timer);
    }, []);

    const formatTime = (s: number) => `${Math.floor(s / 60)}:${(s % 60).toString().padStart(2, '0')}`;

    // Initial greeting
    useEffect(() => {
        if (messages.length === 0 && student) {
            const chapterDisplay = chapterId?.replace(/_/g, ' ').replace(/\bch\d+\s*/i, '');
            setMessages([{
                id: 'init',
                role: 'assistant',
                content: `Hello ${student.name}! 👋\n\nI'm your AI tutor for **${chapterDisplay}**. I'll adapt my explanations to your level.\n\nWhat would you like to learn?`,
                timestamp: new Date(),
            }]);
        }
    }, [student, chapterId]);

    const handleSendMessage = useCallback(async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!input.trim() || !student || !subjectId || !chapterId || isLoading) return;

        const userMsg: Message = {
            id: Date.now().toString(),
            role: 'user',
            content: input,
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsLoading(true);
        setError(null);

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 15000); // 15s frontend timeout

            const response = await chatService.ask(
                student.id,
                userMsg.content,
                subjectId,
                chapterId
            );

            clearTimeout(timeoutId);

            setMessages(prev => [...prev, {
                id: (Date.now() + 1).toString(),
                role: 'assistant',
                content: response.answer,
                timestamp: new Date(),
                difficulty: response.difficulty,
                sources: response.sources,
            }]);
        } catch (err: any) {
            console.error(err);
            const isTimeout = err?.name === 'AbortError' || err?.message?.includes('timeout');
            const errorMsg = isTimeout
                ? "⏱️ The AI is taking too long to respond. Please try a simpler question."
                : "I'm having trouble connecting. Please try again.";

            setError(isTimeout ? 'Request timed out. The AI model may be busy.' : 'Connection error.');
            setMessages(prev => [...prev, {
                id: Date.now().toString(),
                role: 'assistant',
                content: errorMsg,
                timestamp: new Date(),
            }]);
        } finally {
            setIsLoading(false);
            inputRef.current?.focus();
        }
    }, [input, student, subjectId, chapterId, isLoading]);

    const quickQuestions = [
        'Explain the key concepts',
        'Give me an example',
        'What are the applications?',
    ];

    return (
        <div className="flex h-[calc(100vh-4rem)] flex-col bg-slate-50 md:h-screen">
            {/* Header — lightweight */}
            <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 md:px-6">
                <div className="flex items-center gap-3">
                    <button onClick={() => navigate(-1)} className="rounded-lg p-2 text-slate-500 hover:bg-slate-100">
                        <ArrowLeft className="h-5 w-5" />
                    </button>
                    <div>
                        <h1 className="text-lg font-bold text-slate-800 capitalize leading-tight">
                            {chapterId?.replace(/_/g, ' ').replace(/\bch\d+\s*/i, '')}
                        </h1>
                        <p className="text-xs text-slate-500 capitalize flex items-center gap-1">
                            <BookOpen className="h-3 w-3" /> {subjectId}
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-2">
                    <span className="flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-600">
                        <Clock className="h-3 w-3" /> {formatTime(sessionTime)}
                    </span>
                    <span className="flex items-center gap-1 rounded-full bg-violet-50 border border-violet-200 px-3 py-1.5 text-xs font-bold text-violet-600">
                        <Sparkles className="h-3 w-3" /> Adaptive
                    </span>
                </div>
            </header>

            {/* Error banner */}
            {error && (
                <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 text-xs text-amber-700 font-medium">
                    ⚠️ {error}
                </div>
            )}

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto p-4 md:p-6">
                <div className="mx-auto max-w-3xl space-y-4">
                    {messages.map(msg => (
                        <MemoizedChatMessage
                            key={msg.id}
                            role={msg.role}
                            content={msg.content}
                            timestamp={msg.timestamp}
                            difficulty={msg.difficulty}
                            sources={msg.sources}
                        />
                    ))}

                    {isLoading && (
                        <div className="flex items-center gap-3 ml-12">
                            <div className="flex items-center gap-1.5 rounded-2xl bg-white shadow-sm ring-1 ring-slate-100 px-4 py-3">
                                <div className="h-2 w-2 rounded-full bg-violet-400 animate-bounce" />
                                <div className="h-2 w-2 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: '0.15s' }} />
                                <div className="h-2 w-2 rounded-full bg-violet-400 animate-bounce" style={{ animationDelay: '0.3s' }} />
                                <span className="ml-2 text-xs text-slate-500">Thinking...</span>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Quick Suggestions */}
            {messages.length <= 1 && (
                <div className="flex flex-wrap justify-center gap-2 px-4 pb-2">
                    {quickQuestions.map(q => (
                        <button key={q} onClick={() => setInput(q)}
                            className="rounded-full bg-white border border-slate-200 px-4 py-2 text-xs font-medium text-slate-600 hover:bg-blue-50 hover:border-blue-200 hover:text-blue-600 transition-colors">
                            {q}
                        </button>
                    ))}
                </div>
            )}

            {/* Input */}
            <footer className="border-t border-slate-200 bg-white p-4 md:p-6">
                <form onSubmit={handleSendMessage}
                    className="mx-auto flex max-w-3xl items-end gap-3 rounded-2xl bg-slate-100 p-2 ring-1 ring-slate-200 focus-within:ring-2 focus-within:ring-blue-400 transition-shadow">
                    <input
                        ref={inputRef}
                        className="min-h-[44px] w-full bg-transparent px-4 py-3 text-slate-800 placeholder-slate-400 focus:outline-none text-sm"
                        placeholder="Ask anything about this chapter..."
                        value={input}
                        onChange={e => setInput(e.target.value)}
                        disabled={isLoading}
                        autoFocus
                    />
                    <button type="submit" disabled={!input.trim() || isLoading}
                        className={clsx(
                            "mb-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl transition-colors",
                            input.trim()
                                ? "bg-blue-600 text-white hover:bg-blue-700 active:bg-blue-800"
                                : "bg-slate-200 text-slate-400 cursor-not-allowed"
                        )}>
                        <Send className="h-4 w-4" />
                    </button>
                </form>
            </footer>
        </div>
    );
}
