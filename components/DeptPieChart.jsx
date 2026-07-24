import React from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const COLORS = ['#2563eb', '#16a34a', '#d97706', '#dc2626', '#9333ea', '#0891b2'];

export const DeptPieChart = ({ data = [] }) => {
  return (
    <div style={{ background: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
      <h3 style={{ marginTop: 0, marginBottom: '15px', color: '#1e293b' }}>Department Distribution (Pie Chart)</h3>
      <div style={{ width: '100%', height: 300 }}>
        {data.length === 0 ? (
          <p style={{ textAlign: 'center', paddingTop: '100px', color: '#888' }}>No data found</p>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                dataKey="total_value"
                nameKey="department"
                cx="50%"
                cy="50%"
                outerRadius={80}
                label={(entry) => entry.department}
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(v) => [`$${v}`, 'Total Value']} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
};

export default DeptPieChart;