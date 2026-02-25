import clsx from 'clsx';
import { Bot, User, Sparkles } from 'lucide-react';

interface ChatMessageProps {
    role: 'user' | 'assistant';
    content: string;
    timestamp?: Date;
    difficulty?: string;
    sources?: string[];
}

function renderMarkdown(text: string) {
    // Simple markdown: **bold**, *italic*, `code`, - lists
    const lines = text.split('\n');
    return lines.map((line, i) => {
        // Bold
        let processed = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        // Italic
        processed = processed.replace(/\*(.*?)\*/g, '<em>$1</em>');
        // Inline code
        processed = processed.replace(/`(.*?)`/g, '<code class="bg-slate-100 text-blue-700 px-1.5 py-0.5 rounded text-xs font-mono">$1</code>');
        // Bullet points
        if (processed.trim().startsWith('- ') || processed.trim().startsWith('• ')) {
            processed = `<span class="flex gap-2"><span class="text-blue-400 shrink-0">•</span><span>${processed.trim().slice(2)}</span></span>`;
        }
        // Numbered lists
        const numMatch = processed.trim().match(/^(\d+)\.\s(.+)$/);
        if (numMatch) {
            processed = `<span class="flex gap-2"><span class="text-blue-500 font-bold shrink-0">${numMatch[1]}.</span><span>${numMatch[2]}</span></span>`;
        }
        return <p key={i} className="mb-1 last:mb-0" dangerouslySetInnerHTML={{ __html: processed }} />;
    });
}

export function ChatMessage({ role, content, timestamp, difficulty, sources }: ChatMessageProps) {
    const isUser = role === 'user';

    return (
        <div className={clsx('flex w-full gap-3 animate-slide-up', isUser ? 'flex-row-reverse' : '')}>
            {/* Avatar */}
            <div className={clsx(
                'flex h-9 w-9 shrink-0 items-center justify-center rounded-xl shadow-sm',
                isUser
                    ? 'bg-gradient-to-br from-blue-500 to-indigo-600'
                    : 'bg-gradient-to-br from-violet-500 to-purple-600'
            )}>
                {isUser
                    ? <User className="h-4 w-4 text-white" />
                    : <Bot className="h-4 w-4 text-white" />
                }
            </div>

            {/* Message bubble */}
            <div className={clsx('flex max-w-[85%] flex-col', isUser ? 'items-end' : 'items-start')}>
                {/* Header */}
                <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-bold text-slate-700">{isUser ? 'You' : 'AI Tutor'}</span>
                    {timestamp && (
                        <span className="text-[10px] text-slate-400">
                            {timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                    )}
                    {!isUser && difficulty && (
                        <span className={clsx(
                            "flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider",
                            difficulty === 'easy' ? "bg-emerald-100 text-emerald-700" :
                                difficulty === 'medium' ? "bg-amber-100 text-amber-700" :
                                    "bg-red-100 text-red-700"
                        )}>
                            <Sparkles className="h-2.5 w-2.5" />
                            {difficulty}
                        </span>
                    )}
                </div>

                {/* Content */}
                <div className={clsx(
                    'rounded-2xl px-4 py-3 text-sm leading-relaxed',
                    isUser
                        ? 'bg-gradient-to-br from-blue-500 to-indigo-600 text-white rounded-tr-sm'
                        : 'bg-white shadow-md ring-1 ring-slate-100 text-slate-700 rounded-tl-sm'
                )}>
                    {isUser ? (
                        <p className="whitespace-pre-wrap">{content}</p>
                    ) : (
                        <div className="space-y-0.5">{renderMarkdown(content)}</div>
                    )}
                </div>

                {/* Sources */}
                {!isUser && sources && sources.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-2">
                        {sources.slice(0, 3).map((src, i) => (
                            <span key={i} className="inline-flex items-center rounded-full bg-blue-50 px-2.5 py-0.5 text-[10px] font-medium text-blue-600 ring-1 ring-blue-100">
                                📖 {src}
                            </span>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
