import React from 'react';

export const TopMetricsTable = ({ data = [] }) => {
  return (
    <div style={{ background: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
      <h3 style={{ marginTop: 0, marginBottom: '15px', color: '#1e293b' }}>Top Metrics</h3>
      
      {data.length === 0 ? (
        <p style={{ textAlign: 'center', paddingTop: '100px', color: '#888' }}>No data found</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '10px' }}>
          <thead>
            <tr style={{ borderBottom: '2px solid #e2e8f0', textAlign: 'left', color: '#475569' }}>
              <th style={{ padding: '10px' }}>Metric Name</th>
              <th style={{ padding: '10px' }}>Department</th>
              <th style={{ padding: '10px' }}>Value</th>
            </tr>
          </thead>
          <tbody>
            {data.map((item, index) => {
              // Safe checks for all common Department property names
              const deptName =
                item.department ||
                item.dept_name ||
                item.dept ||
                item.department_name ||
                item.Department ||
                item.Dept ||
                'N/A';

              // Safe checks for all common Value property names
              const metricValue =
                item.metric_value ??
                item.value ??
                item.total_value ??
                item.val ??
                item.MetricValue ??
                item.Value ??
                0;

              // Safe checks for Metric Name property
              const metricName =
                item.metric_name ||
                item.name ||
                item.title ||
                item.MetricName ||
                'N/A';

              return (
                <tr key={item.id || index} style={{ borderBottom: '1px solid #f1f5f9' }}>
                  <td style={{ padding: '10px', color: '#334155', fontWeight: '500' }}>
                    {metricName}
                  </td>
                  <td style={{ padding: '10px', color: '#64748b' }}>
                    {deptName}
                  </td>
                  <td style={{ padding: '10px', color: '#16a34a', fontWeight: '600' }}>
                    ${metricValue}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      )}
    </div>
  );
};

export default TopMetricsTable;;