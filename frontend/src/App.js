import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { Toaster } from './components/ui/sonner';
import Layout from './components/Layout';

// Pages
import Login from './pages/Login';
import Register from './pages/Register';
import AuthCallback from './pages/AuthCallback';
import Dashboard from './pages/Dashboard';
import StockDashboard from './pages/StockDashboard';
import Materials from './pages/Materials';
import GRN from './pages/GRN';
import Bins from './pages/Bins';
import Putaway from './pages/Putaway';
import Issues from './pages/Issues';
import Labels from './pages/Labels';
import Reports from './pages/Reports';
import Users from './pages/Users';
import TransferOrders from './pages/TransferOrders';
import WMReports from './pages/WMReports';

// Protected Route wrapper
const ProtectedRoute = ({ children, allowedRoles }) => {
  const { user, loading, hasPermission } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#f9fafb]">
        <div className="animate-pulse text-gray-500">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && !hasPermission(allowedRoles)) {
    return <Navigate to="/dashboard" replace />;
  }

  return <Layout>{children}</Layout>;
};

// Smart Dashboard that shows Stock Dashboard for Management Viewer
const SmartDashboard = () => {
  const { user } = useAuth();
  
  // Management Viewer sees Stock Dashboard as their homepage
  if (user?.role === 'Management Viewer') {
    return <StockDashboard />;
  }
  
  return <Dashboard />;
};

// App Router with session_id check
const AppRouter = () => {
  const location = useLocation();
  
  // Check URL fragment for session_id SYNCHRONOUSLY during render
  // This prevents race conditions with ProtectedRoute
  if (location.hash?.includes('session_id=')) {
    return <AuthCallback />;
  }

  return (
    <Routes>
      {/* Public routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      
      {/* Protected routes */}
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <SmartDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/stock-dashboard"
        element={
          <ProtectedRoute>
            <StockDashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/materials"
        element={
          <ProtectedRoute allowedRoles={['Admin', 'Store In-Charge', 'Inventory Controller', 'Auditor']}>
            <Materials />
          </ProtectedRoute>
        }
      />
      <Route
        path="/grn"
        element={
          <ProtectedRoute allowedRoles={['Admin', 'Store In-Charge', 'Warehouse Operator', 'Inventory Controller', 'Auditor']}>
            <GRN />
          </ProtectedRoute>
        }
      />
      <Route
        path="/bins"
        element={
          <ProtectedRoute allowedRoles={['Admin', 'Store In-Charge', 'Inventory Controller', 'Auditor']}>
            <Bins />
          </ProtectedRoute>
        }
      />
      <Route
        path="/putaway"
        element={
          <ProtectedRoute allowedRoles={['Admin', 'Store In-Charge', 'Warehouse Operator']}>
            <Putaway />
          </ProtectedRoute>
        }
      />
      <Route
        path="/issues"
        element={
          <ProtectedRoute allowedRoles={['Admin', 'Store In-Charge', 'Warehouse Operator']}>
            <Issues />
          </ProtectedRoute>
        }
      />
      <Route
        path="/labels"
        element={
          <ProtectedRoute allowedRoles={['Admin', 'Store In-Charge', 'Warehouse Operator']}>
            <Labels />
          </ProtectedRoute>
        }
      />
      <Route
        path="/reports"
        element={
          <ProtectedRoute allowedRoles={['Admin', 'Store In-Charge', 'Inventory Controller', 'Auditor', 'Management Viewer']}>
            <Reports />
          </ProtectedRoute>
        }
      />
      <Route
        path="/transfer-orders"
        element={
          <ProtectedRoute allowedRoles={['Admin', 'Store In-Charge', 'Warehouse Operator', 'Inventory Controller']}>
            <TransferOrders />
          </ProtectedRoute>
        }
      />
      <Route
        path="/wm-reports"
        element={
          <ProtectedRoute allowedRoles={['Admin', 'Store In-Charge', 'Inventory Controller', 'Auditor', 'Management Viewer']}>
            <WMReports />
          </ProtectedRoute>
        }
      />
      <Route
        path="/users"
        element={
          <ProtectedRoute allowedRoles={['Admin']}>
            <Users />
          </ProtectedRoute>
        }
      />
      
      {/* Redirect root to dashboard */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      
      {/* 404 fallback */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRouter />
        <Toaster position="top-right" richColors />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
