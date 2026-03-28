import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'

// Pages & Layout
import Layout from './components/Layout'
import Login from './pages/Login'
import Register from './pages/Register'
import Loader from './components/common/Loader'

import Dashboard from './pages/Dashboard'
import MenuManagement from './pages/MenuManagement'
import Orders from './pages/Orders'
import ChatHistory from './pages/ChatHistory'
import AutonomyMonitor from './pages/AutonomyMonitor'
import EngagementCampaigns from './pages/EngagementCampaigns'
import AdvancedAnalytics from './pages/AdvancedAnalytics'
import Settings from './pages/Settings'
import DemoRunner from './pages/DemoRunner'

function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) return <div className="min-h-screen flex items-center justify-center bg-gray-50"><Loader /></div>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  
  return children;
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/dashboard" />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/demo" element={<DemoRunner />} />
      
      <Route path="/" element={<ProtectedRoute><Layout /></ProtectedRoute>}>
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="menu" element={<MenuManagement />} />
        <Route path="orders" element={<Orders />} />
        <Route path="chats" element={<ChatHistory />} />
        <Route path="autonomy-monitor" element={<AutonomyMonitor />} />
        <Route path="engagement" element={<EngagementCampaigns />} />
        <Route path="analytics" element={<AdvancedAnalytics />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  )
}

export default App
