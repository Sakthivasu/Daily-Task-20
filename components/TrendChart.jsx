import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
} from 'recharts';

export const TrendChart = ({ data = [], loading = false }) => {
  if (loading) {
    return (
      <div style={{ background: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)', textAlign: 'center', color: '#888' }}>
        Loading Performance Trends...
      </div>
    );
  }

  // Safely normalize and sort incoming backend data
  const formattedData = data
    .map((item) => {
      // Safely extract date property
      const rawDate =
        item.recorded_on ||
        item.recorded_date ||
        item.date ||
        item.month ||
        item.created_at ||
        'N/A';

      let displayDate = rawDate;
      if (rawDate !== 'N/A' && typeof rawDate === 'string') {
        displayDate = rawDate.split('T')[0]; // Format to YYYY-MM-DD
      }

      // Safely extract numeric value
      const rawVal =
        item.metric_value ??
        item.value ??
        item.total_value ??
        item.val ??
        item.total ??
        0;

      return {
        recorded_on: displayDate,
        metric_value: Number(rawVal) || 0,
      };
    })
    .sort((a, b) => new Date(a.recorded_on) - new Date(b.recorded_on));

  return (
    <div style={{ background: '#fff', padding: '20px', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.05)' }}>
      <div style={{ marginBottom: '15px' }}>
        <h3 style={{ margin: 0, color: '#0b0d0f', fontSize: '18px', fontWeight: '600' }}>
          Performance Trends (Line Chart)
        </h3>
      </div>

      {formattedData.length === 0 ? (
        <div style={{ height: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#888' }}>
          No data found
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={320}>
          <LineChart
            data={formattedData}
            margin={{
              top: 15,
              right: 20,
              left: 10,
              bottom: 5,
            }}
          >
            <CartesianGrid
              strokeDasharray="3 3"
              vertical={false}
              stroke="#e5e7eb"
            />

            <XAxis
              dataKey="recorded_on"
              tick={{ fontSize: 12, fill: '#64748b' }}
              axisLine={false}
              tickLine={false}
            />

            <YAxis
              tick={{ fontSize: 12, fill: '#64748b' }}
              axisLine={false}
              tickLine={false}
              domain={['auto', 'auto']}
              tickFormatter={(value) => `$${Number(value).toLocaleString()}`}
            />

            <Tooltip
              formatter={(value) => [
                `$${Number(value).toLocaleString()}`,
                'Value',
              ]}
              contentStyle={{
                backgroundColor: '#ffffff',
                borderRadius: '6px',
                border: '1px solid #cbd5e1',
                boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)',
              }}
            />

            <Line
              type="monotone"
              dataKey="metric_value"
              stroke="#1232a6"
              strokeWidth={3}
              dot={{
                r: 5,
                strokeWidth: 2,
                fill: '#ffffff',
                stroke: '#2129cf',
              }}
              activeDot={{
                r: 8,
                fill: '#bcd4c5',
              }}
              connectNulls={true}
              isAnimationActive={true}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  );
};

export default TrendChart;