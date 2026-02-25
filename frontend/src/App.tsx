import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppLayout } from './components/Layout/AppLayout';
import { ErrorBoundary } from './components/ErrorBoundary';
import { LandingPage } from './pages/LandingPage';
import { StudentSelectPage } from './pages/StudentSelectPage';
import { DashboardPage } from './pages/DashboardPage';
import { SubjectSelectPage } from './pages/SubjectSelectPage';
import { QuizPage } from './pages/QuizPage';
import { LearningPage } from './pages/LearningPage';
import { ChapterSelectPage } from './pages/ChapterSelectPage';
import { VideoLibraryPage } from './pages/VideoLibraryPage';

function App() {
  return (
    <ErrorBoundary>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<StudentSelectPage />} />

          <Route element={<AppLayout />}>
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/subjects" element={<SubjectSelectPage />} />
            <Route path="/subjects/:subjectId/chapters" element={<ChapterSelectPage />} />
            <Route path="/quiz" element={<QuizPage />} />
            <Route path="/learn/:subjectId/:chapterId" element={<LearningPage />} />
            <Route path="/videos" element={<VideoLibraryPage />} />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

export default App;
