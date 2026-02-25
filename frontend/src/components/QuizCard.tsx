import clsx from 'clsx';

interface QuizCardProps {
    question: string;
    options: string[];
    selectedOption?: string | null;
    onSelectOption: (option: string) => void;
    isLocked?: boolean;
}

export function QuizCard({ question, options, selectedOption, onSelectOption, isLocked = false }: QuizCardProps) {
    return (
        <div className="w-full rounded-xl bg-white p-6 shadow-sm border border-slate-200">
            <h3 className="mb-6 text-xl font-semibold text-slate-800">{question}</h3>

            <div className="space-y-3">
                {options.map((option, index) => {
                    const isSelected = selectedOption === option;

                    return (
                        <button
                            key={index}
                            onClick={() => !isLocked && onSelectOption(option)}
                            disabled={isLocked}
                            className={clsx(
                                'flex w-full items-center rounded-lg border px-4 py-3 text-left transition-all',
                                isSelected
                                    ? 'border-blue-500 bg-blue-50 text-blue-700 ring-1 ring-blue-500'
                                    : 'border-slate-200 hover:bg-slate-50 hover:border-slate-300',
                                isLocked && 'cursor-not-allowed opacity-60'
                            )}
                        >
                            <span
                                className={clsx(
                                    'mr-3 flex h-6 w-6 items-center justify-center rounded-full border text-sm font-medium',
                                    isSelected
                                        ? 'border-blue-500 bg-blue-500 text-white'
                                        : 'border-slate-300 text-slate-500'
                                )}
                            >
                                {String.fromCharCode(65 + index)}
                            </span>
                            <span className="font-medium">{option}</span>
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
