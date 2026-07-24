import React, { useState, useEffect } from 'react';
import { io } from 'socket.io-client';
import api from '../api'; // Your axios instance

const socket = io('http://localhost:5000', {
  transports: ['websocket', 'polling']
});

// Helper function to convert raw timestamps into relative time (e.g., "Just now", "5 mins ago", "2 hours ago")
const formatTimeAgo = (timestamp) => {
  if (!timestamp) return '';

  const now = new Date();
  const date = new Date(timestamp);
  const seconds = Math.floor((now - date) / 1000);

  if (isNaN(seconds)) return timestamp; // Return raw value if parsing fails

  if (seconds < 10) return 'Just now';
  if (seconds < 60) return `${seconds} secs ago`;

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} ${minutes === 1 ? 'min' : 'mins'} ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} ${hours === 1 ? 'hour' : 'hours'} ago`;

  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} ${days === 1 ? 'day' : 'days'} ago`;

  const months = Math.floor(days / 30);
  if (months < 12) return `${months} ${months === 1 ? 'month' : 'months'} ago`;

  const years = Math.floor(days / 365);
  return `${years} ${years === 1 ? 'year' : 'years'} ago`;
};

export const NotificationBell = () => {
  const [notifications, setNotifications] = useState([]);
  const [open, setOpen] = useState(false);

  // Fetch initial notifications
  useEffect(() => {
    fetchNotifications();

    // Listen for real-time WebSocket events from Flask backend
    socket.on('activity_update', (newActivity) => {
      setNotifications((prev) => [newActivity, ...prev]);
    });

    return () => socket.off('activity_update');
  }, []);

  const fetchNotifications = async () => {
    try {
      const res = await api.get('/notifications');
      setNotifications(res.data);
    } catch (err) {
      console.error('Error fetching notifications:', err);
    }
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    try {
      await api.delete(`/notifications/${id}`);
      setNotifications(notifications.filter((item) => item.id !== id));
    } catch (err) {
      console.error('Error deleting notification:', err);
    }
  };

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      {/* Bell Icon Button */}
      <button 
        onClick={() => setOpen(!open)} 
        style={{ background: 'none', border: 'none', fontSize: '20px', cursor: 'pointer', position: 'relative' }}
      >
        🔔
        {notifications.length > 0 && (
          <span style={{
            position: 'absolute', top: '-5px', right: '-5px',
            background: 'red', color: 'white', borderRadius: '50%',
            padding: '2px 6px', fontSize: '10px'
          }}>
            {notifications.length}
          </span>
        )}
      </button>

      {/* Notifications Dropdown */}
      {open && (
        <div style={{
          position: 'absolute', right: 0, top: '35px', width: '320px',
          background: '#fff', border: '1px solid #ccc', borderRadius: '8px',
          boxShadow: '0 4px 8px rgba(0,0,0,0.1)', zIndex: 1000, maxHeight: '350px', overflowY: 'auto'
        }}>
          <div style={{ padding: '10px', borderBottom: '1px solid #eee', fontWeight: 'bold' }}>
            Notifications
          </div>
          {notifications.length === 0 ? (
            <div style={{ padding: '10px', textAlign: 'center', color: '#888' }}>No notifications</div>
          ) : (
            notifications.map((item) => (
              <div key={item.id} style={{
                padding: '10px', borderBottom: '1px solid #eee',
                display: 'flex', justifyContent: 'space-between', alignItems: 'center'
              }}>
                <div>
                  <p style={{ margin: 0, fontSize: '13px' }}>
                    <strong>{item.user_name}:</strong> {item.action}
                  </p>
                  {/* Formatted Relative Time */}
                  <small style={{ color: '#888', fontSize: '11px' }}>
                    {formatTimeAgo(item.created_at)}
                  </small>
                </div>
                <button 
                  onClick={(e) => handleDelete(item.id, e)}
                  style={{ background: 'transparent', border: 'none', color: 'red', cursor: 'pointer', fontWeight: 'bold' }}
                >
                  ✕
                </button>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default NotificationBell;