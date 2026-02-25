import api from './api';

export interface ChatResponse {
    answer: string;
    sources: any[];
    student_xp: number;
    difficulty: string;
}

export const chatService = {
    ask: async (studentId: string, question: string, subject: string, chapterId: string): Promise<ChatResponse> => {
        const response = await api.post<ChatResponse>('/ask', {
            student_id: studentId,
            question,
            subject,
            chapter_id: chapterId
        });
        return response.data;
    }
};
