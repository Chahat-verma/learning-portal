import { create } from 'zustand';


interface QuizState {
    currentQuizId: string | null;
    currentQuestionIndex: number;
    answers: Record<string, string>;
    isCompleted: boolean;
    score: number;
    actions: {
        startQuiz: (quizId: string) => void;
        submitAnswer: (questionId: string, answer: string) => void;
        completeQuiz: (score: number) => void;
        resetQuiz: () => void;
    };
}

export const useQuizStore = create<QuizState>((set) => ({
    currentQuizId: null,
    currentQuestionIndex: 0,
    answers: {},
    isCompleted: false,
    score: 0,
    actions: {
        startQuiz: (quizId) => set({
            currentQuizId: quizId,
            currentQuestionIndex: 0,
            answers: {},
            isCompleted: false,
            score: 0
        }),
        submitAnswer: (questionId, answer) => set((state) => ({
            answers: { ...state.answers, [questionId]: answer }
        })),
        completeQuiz: (score) => set({ isCompleted: true, score }),
        resetQuiz: () => set({
            currentQuizId: null,
            currentQuestionIndex: 0,
            answers: {},
            isCompleted: false,
            score: 0
        }),
    },
}));
