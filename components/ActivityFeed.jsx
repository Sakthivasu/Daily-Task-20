import React, { useEffect, useState, useContext } from 'react';
import api from '../api';
import { SocketContext } from '../context/SocketContext';

export const ActivityFeed = () => {
  const [activities, setActivities] = useState([]);
  const socket = useContext(SocketContext);

  useEffect(() => {
    api.get('/activity').then((res) => setActivities(res.data));
  }, []);

  useEffect(() => {
    if (!socket) return;
    socket.on('activity_update', (item) => {
      setActivities((prev) => [item, ...prev.slice(0, 19)]);
    });
    return () => socket.off('activity_update');
  }, [socket]);

  return (
    <div className="activity-feed">
      <h3>Live Platform Activity</h3>
      <ul>
        {activities.map((a, i) => (
          <li key={i}>
            <strong>{a.user_name}</strong> {a.action}
            <span className="time">{a.created_at}</span>
          </li>
        ))}
      </ul>
    </div>
  );
};
