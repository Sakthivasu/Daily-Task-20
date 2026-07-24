import React, { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';

export const RoleRoute = ({ children, allowedRoles }) => {
  const { user } = useContext(AuthContext);

  if (!user || !allowedRoles.includes(user.role)) {
    return (
      <div className="error-403">
        <h2>403 — Access Forbidden</h2>
        <p>You do not have permission to access this page.</p>
      </div>
    );
  }

  return children;
};