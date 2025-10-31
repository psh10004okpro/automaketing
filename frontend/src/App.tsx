import { Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { useAuthStore } from './stores/authStore';
import { authAPI } from './services/api';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import EnhancedDashboard from './pages/EnhancedDashboard';
import Campaigns from './pages/Campaigns';
import AIContentGenerator from './pages/AIContentGenerator';
import Leads from './pages/Leads';
import Workflows from './pages/Workflows';
import SMSCampaigns from './pages/SMSCampaigns';
import SocialMedia from './pages/SocialMedia';
import Layout from './components/Layout';

// Protected Route wrapper
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuthStore();

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}

function App() {
  const { setUser, isAuthenticated } = useAuthStore();

  useEffect(() => {
    // Check if user is logged in on mount
    const token = localStorage.getItem('access_token');
    if (token) {
      authAPI
        .getCurrentUser()
        .then((response) => {
          setUser(response.data);
        })
        .catch(() => {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
        });
    }
  }, [setUser]);

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Protected routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<EnhancedDashboard />} />
        <Route path="campaigns" element={<Campaigns />} />
        <Route path="sms" element={<SMSCampaigns />} />
        <Route path="social" element={<SocialMedia />} />
        <Route path="leads" element={<Leads />} />
        <Route path="workflows" element={<Workflows />} />
        <Route path="ai-content" element={<AIContentGenerator />} />
      </Route>

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default App;
