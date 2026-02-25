import api from './api';
import type { Subject, Chapter } from '@/types';

export const contentService = {
    getSubjects: async (): Promise<Subject[]> => {
        const response = await api.get<Subject[]>('/subjects');
        return response.data;
    },

    getChapters: async (subjectId: string): Promise<Chapter[]> => {
        const response = await api.get<Chapter[]>(`/subjects/${subjectId}/chapters`);
        return response.data;
    }
};
