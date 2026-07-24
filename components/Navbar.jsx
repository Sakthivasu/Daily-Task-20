import React, { useContext } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { AuthContext } from '../context/AuthContext';
import { ThemeContext } from '../context/ThemeContext';
import { NotificationBell } from './NotificationBell';

export const Navbar = () => {
  const { user, logout } = useContext(AuthContext);
  const { theme, toggleTheme } = useContext(ThemeContext);
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <nav className="navbar" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 20px', borderBottom: '1px solid #e2e8f0' }}>
      <div className="nav-brand">
        <Link to="/dashboard" style={{ textDecoration: 'none', fontWeight: 'bold', fontSize: '18px' }}>EDABIP Mini</Link>
      </div>
      
      <div className="nav-links" style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
        <Link 
          to="/dashboard" 
          style={{ textDecoration: 'none', color: location.pathname === '/dashboard' ? '#2563eb' : '#475569', fontWeight: location.pathname === '/dashboard' ? 'bold' : 'normal' }}
        >
          Dashboard
        </Link>
        
        {(user?.role === 'admin' || user?.role === 'analyst') && (
          <Link 
            to="/data" 
            style={{ textDecoration: 'none', color: location.pathname === '/data' ? '#2563eb' : '#475569', fontWeight: location.pathname === '/data' ? 'bold' : 'normal' }}
          >
            Data Management
          </Link>
        )}

        <Link
          to="/profile"
          style={{ textDecoration: 'none', color: location.pathname === '/profile' ? '#2563eb' : '#475569', fontWeight: location.pathname === '/profile' ? 'bold' : 'normal' }}
        >
          Profile
        </Link>
      </div>

      <div className="nav-actions" style={{ display: 'flex', gap: '15px', alignItems: 'center' }}>
        <NotificationBell />
        
        <button 
          className="theme-toggle" 
          onClick={toggleTheme}
          style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '16px' }}
        >
          {theme === 'light' ? '🌙' : '☀️'}
        </button>

        <Link to="/profile" className="nav-profile" style={{ display: 'flex', alignItems: 'center', gap: '8px', textDecoration: 'none', color: '#334155' }}>
          <img
            src={user?.avatar_url ? `http://localhost:5000${user.avatar_url}` : 'https://via.placeholder.com/35'}
            alt="avatar"
            className="avatar-img"
            style={{ width: '35px', height: '35px', borderRadius: '50%', objectFit: 'cover' }}
          />
          <span style={{ fontWeight: '500' }}>{user?.name || 'User'}</span>
        </Link>

        <button 
          onClick={handleLogout} 
          className="btn-logout"
          style={{ padding: '6px 12px', background: '#dc2626', color: '#fff', border: 'none', borderRadius: '4px', cursor: 'pointer' }}
        >
          Logout
        </button>
      </div>
    </nav>
  );
};

export default Navbar;