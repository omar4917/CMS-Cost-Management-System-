import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { AuthProvider, useAuth } from './context/AuthContext';
import { CurrencyProvider } from './context/CurrencyContext';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ProjectsPage from './pages/ProjectsPage';
import InvestorsPage from './pages/InvestorsPage';
import InvestmentsPage from './pages/InvestmentsPage';
import PaymentSchedulesPage from './pages/PaymentSchedulesPage';
import CostCategoriesPage from './pages/CostCategoriesPage';
import ContractorsPage from './pages/ContractorsPage';
import DocumentsPage from './pages/DocumentsPage';
import EmailsPage from './pages/EmailsPage';
import AuditLogsPage from './pages/AuditLogsPage';
import BackupPage from './pages/BackupPage';
import SettingsPage from './pages/SettingsPage';
import UsersPage from './pages/UsersPage';
import PlaceholderPage from './pages/PlaceholderPage';

function ProtectedRoute({ children }) {
    const { user, loading } = useAuth();
    if (loading) return <div className="loading-spinner"><div className="spinner"></div></div>;
    if (!user) return <Navigate to="/login" />;
    return children;
}

function AppLayout({ children }) {
    return (
        <CurrencyProvider>
            <div className="app-layout">
                <Sidebar />
                <div className="main-content">
                    <Header />
                    {children}
                </div>
            </div>
        </CurrencyProvider>
    );
}

function P({ children }) {
    return <ProtectedRoute><AppLayout>{children}</AppLayout></ProtectedRoute>;
}

function AppRoutes() {
    const { user } = useAuth();

    return (
        <Routes>
            <Route path="/login" element={user ? <Navigate to="/" /> : <LoginPage />} />
            <Route path="/" element={<P><DashboardPage /></P>} />
            <Route path="/projects" element={<P><ProjectsPage /></P>} />
            <Route path="/projects/:id" element={<P><PlaceholderPage title="Project Details" description="Detailed project view with costs, milestones, and investors" /></P>} />
            <Route path="/investors" element={<P><InvestorsPage /></P>} />
            <Route path="/investments" element={<P><InvestmentsPage /></P>} />
            <Route path="/payment-schedules" element={<P><PaymentSchedulesPage /></P>} />
            <Route path="/cost-categories" element={<P><CostCategoriesPage /></P>} />
            <Route path="/contractors" element={<P><ContractorsPage /></P>} />
            <Route path="/documents" element={<P><DocumentsPage /></P>} />
            <Route path="/emails" element={<P><EmailsPage /></P>} />
            <Route path="/reports" element={<P><PlaceholderPage title="Reports & Analytics" description="PDF reports and exports — coming in Phase 4" /></P>} />
            <Route path="/audit-logs" element={<P><AuditLogsPage /></P>} />
            <Route path="/backup" element={<P><BackupPage /></P>} />
            <Route path="/settings" element={<P><SettingsPage /></P>} />
            <Route path="/users" element={<P><UsersPage /></P>} />
            <Route path="*" element={<Navigate to="/" />} />
        </Routes>
    );
}

export default function App() {
    return (
        <Router>
            <AuthProvider>
                <AppRoutes />
                <ToastContainer position="top-right" autoClose={3000} hideProgressBar={false} theme="dark" />
            </AuthProvider>
        </Router>
    );
}
