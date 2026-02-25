export interface Student {
    id: string;
    name: string;
    xp?: number;
    level?: number;
    current_difficulty?: 'easy' | 'medium' | 'hard';
    grade_level?: string;
}

export interface UserState {
    student: Student | null;
    isAuthenticated: boolean;
    login: (student: Student) => void;
    logout: () => void;
}

export interface QuizResult {
    score: number;
    total: number;
    xp_gained: number;
}

export interface Chapter {
    id: string;
    name: string;
    description: string;
}

export interface Subject {
    id: string;
    name: string;
    icon: string;
    color: string;
    chapters?: Chapter[];
}

export interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    difficulty?: string;
    sources?: any[];
}
