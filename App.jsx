import React from 'react';
import { Routes, Route, Navigate, Outlet } from 'react-router-dom';
import { ProtectedRoute } from './components/ProtectedRoute';
import { RoleRoute } from './components/RoleRoute';
import { Navbar } from './components/Navbar';
import { LoginPage } from './pages/LoginPage';
import { Dashboard } from './pages/Dashboard';
import { DataManagement } from './pages/DataManagement';
import { ProfilePage } from './pages/ProfilePage';

// Layout shell for protected routes with persistent Navbar
function AppLayout() {
  return (
    <div className="app-shell">
      <Navbar />
      <main className="content">
        {/* Render child routes inside Outlet */}
        <Outlet />
      </main>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      {/* Public Route */}
      <Route path="/login" element={<LoginPage />} />

      {/* Protected Layout Routes */}
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route
          path="/data"
          element={
            <RoleRoute allowedRoles={['admin', 'analyst']}>
              <DataManagement />
            </RoleRoute>
          }
        />
        <Route path="/profile" element={<ProfilePage />} />
      </Route>

      {/* Default Fallback Redirects */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}