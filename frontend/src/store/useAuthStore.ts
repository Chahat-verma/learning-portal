import { create } from 'zustand';
import type { UserState, Student } from '@/types';

export const useAuthStore = create<UserState>((set) => ({
    student: null,
    isAuthenticated: false,
    login: (student: Student) => set({ student, isAuthenticated: true }),
    logout: () => set({ student: null, isAuthenticated: false }),
}));
