import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
} from 'recharts';

const COLORS = ['#2563eb', '#16a34a', '#d97706', '#dc2626', '#9333ea', '#0891b2', '#0284c7'];

export const DeptBarChart = ({ data = [], loading = false, selectedDepartment = 'All Departments' }) => {
  if (loading) {
    return (
      <div style={{ background: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)', textAlign: 'center', color: '#888', height: 320, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        Loading Department Totals...
      </div>
    );
  }

  // Group & Aggregate Data
  const aggregatedMap = data.reduce((acc, item) => {
    const deptName =
      item.department ||
      item.dept_name ||
      item.dept ||
      item.department_name ||
      item.Department ||
      'N/A';

    const val = Number(
      item.total_value ??
      item.metric_value ??
      item.value ??
      item.val ??
      0
    );

    if (!acc[deptName]) {
      acc[deptName] = 0;
    }
    acc[deptName] += isNaN(val) ? 0 : val;

    return acc;
  }, {});

  const formattedData = Object.keys(aggregatedMap).map((dept) => ({
    department: dept,
    total_value: aggregatedMap[dept],
  }));

  // Force chart update using both selectedDepartment prop and data length stringified
  const chartKey = `${selectedDepartment}-${JSON.stringify(formattedData)}`;

  return (
    <div style={{ background: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
      <div style={{ marginBottom: '15px' }}>
        <h3 style={{ margin: 0, color: '#1e293b', fontSize: '18px', fontWeight: '600' }}>
          Department Totals {selectedDepartment !== 'All Departments' && selectedDepartment !== 'All' ? `(${selectedDepartment})` : ''}
        </h3>
      </div>

      {formattedData.length === 0 ? (
        <div style={{ height: 320, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#888' }}>
          No data found for {selectedDepartment}
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={320}>
          <BarChart
            key={chartKey}
            data={formattedData}
            margin={{ top: 15, right: 20, left: 10, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e5e7eb" />
            <XAxis dataKey="department" tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 12, fill: '#64748b' }} axisLine={false} tickLine={false} domain={[0, 'auto']} tickFormatter={(value) => `$${Number(value).toLocaleString()}`} />
            <Tooltip formatter={(value) => [`$${Number(value).toLocaleString()}`, 'Total Value']} contentStyle={{ backgroundColor: '#ffffff', borderRadius: '6px', border: '1px solid #cbd5e1' }} />
            <Bar dataKey="total_value" radius={[6, 6, 0, 0]} barSize={formattedData.length === 1 ? 50 : undefined}>
              {formattedData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};

export default DeptBarChart;