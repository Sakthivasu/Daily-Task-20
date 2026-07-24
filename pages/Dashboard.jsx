import React, { useEffect, useState } from 'react';
import api from '../api';
import { FilterBar } from '../components/FilterBar';
import { KPICards } from '../components/KPICards';
import { TrendChart } from '../components/TrendChart';
import { DeptBarChart } from '../components/DeptBarChart';
import { DeptPieChart } from '../components/DeptPieChart';
import TopMetricsTable from '../components/TopMetricsTable';
import { ActivityFeed } from '../components/ActivityFeed';

export const Dashboard = () => {
  const [departments, setDepartments] = useState([]);
  const [filters, setFilters] = useState({ department: '', from: '', to: '' });
  const [kpis, setKpis] = useState({});
  const [trend, setTrend] = useState([]);
  const [deptData, setDeptData] = useState([]);
  const [topMetrics, setTopMetrics] = useState([]);
  const [loading, setLoading] = useState(true);

  // 1. Load Departments for Filter Bar Dropdown
  useEffect(() => {
    api
      .get('/departments')
      .then((res) => setDepartments(res.data || []))
      .catch((err) => console.error('Error loading departments:', err));
  }, []);

  // 2. Fetch Filtered Data whenever 'filters' State changes
  useEffect(() => {
    setLoading(true);

    const cleanParams = {};
    if (
      filters.department &&
      filters.department !== 'All' &&
      filters.department !== 'all' &&
      filters.department !== 'All Departments'
    ) {
      cleanParams.department = filters.department;
    }
    if (filters.from) cleanParams.from = filters.from;
    if (filters.to) cleanParams.to = filters.to;

    const queryParams = new URLSearchParams(cleanParams).toString();

    Promise.all([
      api.get(`/kpis?${queryParams}`),
      api.get(`/metrics/trend?${queryParams}`),
      api.get(`/metrics/by-department?${queryParams}`),
      api.get(`/metrics/top?${queryParams}`),
    ])
      .then(([resKpi, resTrend, resDept, resTop]) => {
        setKpis(resKpi.data || {});
        setTrend(resTrend.data || []);

        let rawDeptData = resDept.data || [];
        let rawTopMetrics = resTop.data || [];

        const selectedDept = filters.department;
        const isFiltered =
          selectedDept &&
          selectedDept !== 'All' &&
          selectedDept !== 'all' &&
          selectedDept !== 'All Departments';

        // Client-side fallback filter for Department Chart Data
        if (isFiltered) {
          const filteredDeptData = rawDeptData.filter((item) => {
            const itemDept = String(
              item.department ||
                item.dept_name ||
                item.dept ||
                item.department_name ||
                item.Department ||
                ''
            )
              .trim()
              .toLowerCase();

            const targetDept = String(selectedDept).trim().toLowerCase();
            return itemDept === targetDept || itemDept.includes(targetDept);
          });

          if (filteredDeptData.length > 0) {
            rawDeptData = filteredDeptData;
          }
        }

        // Client-side fallback filter for Top Metrics Leaderboard Data
        if (isFiltered) {
          const filteredTopMetrics = rawTopMetrics.filter((item) => {
            const itemDept = String(
              item.department ||
                item.dept_name ||
                item.dept ||
                item.department_name ||
                item.Department ||
                ''
            )
              .trim()
              .toLowerCase();

            const targetDept = String(selectedDept).trim().toLowerCase();
            return itemDept === targetDept || itemDept.includes(targetDept);
          });

          if (filteredTopMetrics.length > 0) {
            rawTopMetrics = filteredTopMetrics;
          }
        }

        setDeptData(rawDeptData);
        setTopMetrics(rawTopMetrics);
      })
      .catch((error) => {
        console.error('API Error:', error.response?.data || error.message);
      })
      .finally(() => setLoading(false));
  }, [filters]);

  return (
    <div className="dashboard-container">
      <h2 className="dashboard-title">Enterprise Dashboard</h2>

      {/* 1. Main Filter Bar */}
      <FilterBar
        departments={departments}
        filters={filters}
        setFilters={setFilters}
      />

      {/* 2. KPI Cards */}
      <KPICards kpis={kpis} loading={loading} />

      {/* 3. Charts Section - Row 1 */}
      <div className="charts-grid">
        <TrendChart data={trend} loading={loading} />
        {/* Pass key prop to force chart re-render on filter change */}
        <DeptBarChart key={`bar-${filters.department}`} data={deptData} loading={loading} />
      </div>

      {/* 4. Charts Section - Row 2 */}
      <div className="charts-grid">
        <DeptPieChart key={`pie-${filters.department}`} data={deptData} loading={loading} />
        <TopMetricsTable
          data={topMetrics}
          selectedDepartment={filters.department || 'All Departments'}
          loading={loading}
        />
      </div>

      {/* 5. Activity Feed */}
      <div style={{ marginTop: '24px' }}>
        <ActivityFeed />
      </div>
    </div>
  );
};

export default Dashboard;