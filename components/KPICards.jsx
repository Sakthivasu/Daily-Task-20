import React from 'react';

export const KPICards = ({ kpis, loading }) => {
  if (loading) return <div className="kpi-skeleton">Loading metrics...</div>;

  return (
    <div className="kpi-grid">
      {/* 1. Total Metric Value */}
      <div className="kpi-card">
        <h3>Total Metric Value</h3>
        <p className="kpi-value">
          ${Number(kpis.total_value || 0).toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}
        </p>
      </div>

      {/* 2. Total Records Value */}
      <div className="kpi-card">
        <h3>Total Records Value</h3>
        <p className="kpi-value">{kpis.total_records || 0}</p>
      </div>

      {/* 3. Average Metric Value */}
      <div className="kpi-card">
        <h3>Average Value</h3>
        <p className="kpi-value">
          ${Number(kpis.average_value || 0).toLocaleString(undefined, {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          })}
        </p>
      </div>

      {/* 4. Month-over-Month Growth Change */}
      <div className="kpi-card">
        <h3>MoM Growth Rate</h3>
        <p className={`kpi-value ${kpis.mom_change_pct >= 0 ? 'text-green' : 'text-red'}`}>
          {kpis.mom_change_pct >= 0 ? '↑' : '↓'} {kpis.mom_change_pct}%
        </p>
      </div>
    </div>
  );
};

export default KPICards;