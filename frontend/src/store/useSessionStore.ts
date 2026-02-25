import { create } from 'zustand';

interface SessionState {
    studyTime: number; // in minutes
    xp: number;
    streak: number;
    actions: {
        addXP: (amount: number) => void;
        incrementStudyTime: (minutes: number) => void;
    };
}

export const useSessionStore = create<SessionState>((set) => ({
    studyTime: 0,
    xp: 0,
    streak: 0,
    actions: {
        addXP: (amount) => set((state) => ({ xp: state.xp + amount })),
        incrementStudyTime: (minutes) => set((state) => ({ studyTime: state.studyTime + minutes })),
    },
}));
