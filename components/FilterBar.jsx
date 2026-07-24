import React from 'react';

export const FilterBar = ({ departments, filters, setFilters }) => {
  return (
    <div className="filter-bar">
      <select
        value={filters.department}
        onChange={(e) => setFilters((prev) => ({ ...prev, department: e.target.value }))}
      >
        <option value="">All Departments</option>
        {departments.map((d) => (
          <option key={d.id} value={d.id}>{d.name}</option>
        ))}
      </select>
      <input
        type="date"
        value={filters.from}
        onChange={(e) => setFilters((prev) => ({ ...prev, from: e.target.value }))}
      />
      <input
        type="date"
        value={filters.to}
        onChange={(e) => setFilters((prev) => ({ ...prev, to: e.target.value }))}
      />
    </div>
  );
};
