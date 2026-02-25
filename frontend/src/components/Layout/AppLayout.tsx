import { Outlet, useLocation } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useAuthStore } from '../../store/useAuthStore';

export function AppLayout() {
    const { isAuthenticated } = useAuthStore();
    const location = useLocation();
    const isPublicPage = ['/', '/login'].includes(location.pathname);

    if (!isAuthenticated || isPublicPage) {
        return (
            <main className="min-h-screen bg-slate-50">
                <Outlet />
            </main>
        );
    }

    return (
        <div className="flex h-screen overflow-hidden bg-slate-50">
            <Sidebar />
            <div className="flex flex-1 flex-col overflow-hidden">
                <Header />
                <main className="flex-1 overflow-y-auto p-6">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}
