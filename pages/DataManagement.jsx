import React, { useState, useEffect, useContext } from 'react';
import api from '../api';
import { AuthContext } from '../context/AuthContext';
import { useForm } from '../hooks/useForm';
import { useToast } from '../hooks/useToast';
import { useDebounce } from '../hooks/useDebounce';
import { Pagination } from '../components/Pagination';
import { ToastContainer } from '../components/ToastContainer';

export const DataManagement = () => {
  const { user } = useContext(AuthContext);
  const { toasts, addToast } = useToast();
  const { values, handleChange, resetForm } = useForm({
    department_id: '',
    metric_name: '',
    metric_value: '',
    recorded_on: ''
  });

  const [departments, setDepartments] = useState([]);
  const [records, setRecords] = useState([]);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [search, setSearch] = useState('');
  const debouncedSearch = useDebounce(search, 500);

  const [csvFile, setCsvFile] = useState(null);
  const [previewRows, setPreviewRows] = useState([]);

  // States for Edit Modal
  const [editingRecord, setEditingRecord] = useState(null);
  const [editFormData, setEditFormData] = useState({
    metric_name: '',
    metric_value: '',
    recorded_on: ''
  });

  useEffect(() => {
    api.get('/departments').then((res) => setDepartments(res.data));
  }, []);

  const fetchRecords = () => {
    api.get(`/metrics?page=${page}&limit=10&search=${debouncedSearch}`)
      .then((res) => {
        setRecords(res.data.data);
        setPages(res.data.pages);
      });
  };

  useEffect(() => {
    fetchRecords();
  }, [page, debouncedSearch]);

  const handleAddMetric = async (e) => {
    e.preventDefault();
    try {
      await api.post('/metrics', values);
      addToast('Metric added successfully!', 'success');
      resetForm();
      fetchRecords();
    } catch (err) {
      addToast('Failed to add metric', 'error');
    }
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setCsvFile(file);
      const reader = new FileReader();
      reader.onload = (event) => {
        const text = event.target.result;
        const rows = text.split('\n').slice(0, 6).map((r) => r.split(','));
        setPreviewRows(rows);
      };
      reader.readAsText(file);
    }
  };

  const handleUploadCsv = async () => {
    if (!csvFile) return;
    const formData = new FormData();
    formData.append('file', csvFile);

    try {
      const res = await api.post('/metrics/upload', formData);
      addToast(res.data.message, 'success');
      setCsvFile(null);
      setPreviewRows([]);
      fetchRecords();
    } catch (err) {
      addToast('CSV Upload failed', 'error');
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Delete this record?')) {
      try {
        await api.delete(`/metrics/${id}`);
        addToast('Record deleted', 'info');
        fetchRecords();
      } catch (err) {
        addToast('Failed to delete record', 'error');
      }
    }
  };

  // Open Edit Modal with selected record details
  const handleEditClick = (record) => {
    setEditingRecord(record);
    setEditFormData({
      metric_name: record.metric_name,
      metric_value: record.metric_value,
      recorded_on: record.recorded_on
    });
  };

  // Submit Edit Form
  const handleUpdateSubmit = async (e) => {
    e.preventDefault();
    try {
      await api.put(`/metrics/${editingRecord.id}`, editFormData);
      addToast('Record updated successfully!', 'success');
      setEditingRecord(null);
      fetchRecords();
    } catch (err) {
      addToast('Failed to update record', 'error');
    }
  };

  return (
    <div className="data-management-container">
      <ToastContainer toasts={toasts} />
      <h2 className="page-title">Data Management Center</h2>

      <div className="card">
        <h3>Add Single Metric Record</h3>
        <form onSubmit={handleAddMetric} className="inline-form">
          <select name="department_id" value={values.department_id} onChange={handleChange} required>
            <option value="">Select Dept</option>
            {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
          </select>
          <input name="metric_name" placeholder="Metric Name" value={values.metric_name} onChange={handleChange} required />
          <input name="metric_value" type="number" placeholder="Value" value={values.metric_value} onChange={handleChange} required />
          <input name="recorded_on" type="date" value={values.recorded_on} onChange={handleChange} required />
          <button type="submit" className="btn-primary">Add Record</button>
        </form>
      </div>

      <div className="card">
        <h3>Bulk CSV Upload</h3>
        <input type="file" accept=".csv" onChange={handleFileChange} />
        {previewRows.length > 0 && (
          <div className="preview-section" style={{ marginTop: '16px' }}>
            <h4>CSV Preview (First 5 Rows)</h4>
            <table className="data-table">
              <tbody>
                {previewRows.map((r, i) => (
                  <tr key={i}>{r.map((c, j) => <td key={j}>{c}</td>)}</tr>
                ))}
              </tbody>
            </table>
            <button onClick={handleUploadCsv} className="btn-primary" style={{ marginTop: '12px' }}>
              Upload All
            </button>
          </div>
        )}
      </div>

      <div className="card">
        <h3>Metric Records Database</h3>
        <input
          type="text"
          placeholder="Search metrics..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="search-input"
        />
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Department</th>
              <th>Name</th>
              <th>Value</th>
              <th>Date</th>
              <th>Uploaded By</th>
              {user?.role === 'admin' && <th>Actions</th>}
            </tr>
          </thead>
          <tbody>
            {records.map((r) => (
              <tr key={r.id}>
                <td>{r.id}</td>
                <td>{r.department}</td>
                <td>{r.metric_name}</td>
                <td>${r.metric_value}</td>
                <td>{r.recorded_on}</td>
                <td>{r.uploader}</td>
                {user?.role === 'admin' && (
                  <td style={{ display: 'flex', gap: '8px' }}>
                    <button onClick={() => handleEditClick(r)} className="btn-primary" style={{ padding: '4px 8px' }}>
                      Edit
                    </button>
                    <button onClick={() => handleDelete(r.id)} className="btn-danger" style={{ padding: '4px 8px' }}>
                      Delete
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
        <Pagination page={page} pages={pages} onPageChange={setPage} />
      </div>

      {/* EDIT RECORD MODAL POPUP */}
      {editingRecord && (
        <div style={{
          position: 'fixed', top: 0, left: 0, width: '100%', height: '100%',
          backgroundColor: 'rgba(0, 0, 0, 0.5)', display: 'flex',
          justifyContent: 'center', alignItems: 'center', zIndex: 1000
        }}>
          <div style={{ background: '#fff', padding: '24px', borderRadius: '8px', width: '380px', boxShadow: '0 4px 6px rgba(0,0,0,0.1)' }}>
            <h3>Edit Record #{editingRecord.id}</h3>
            <form onSubmit={handleUpdateSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginTop: '15px' }}>
              <div>
                <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Metric Name</label>
                <input
                  type="text"
                  className="search-input"
                  style={{ width: '100%', marginTop: '4px' }}
                  value={editFormData.metric_name}
                  onChange={(e) => setEditFormData({ ...editFormData, metric_name: e.target.value })}
                  required
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Value ($)</label>
                <input
                  type="number"
                  step="0.01"
                  className="search-input"
                  style={{ width: '100%', marginTop: '4px' }}
                  value={editFormData.metric_value}
                  onChange={(e) => setEditFormData({ ...editFormData, metric_value: e.target.value })}
                  required
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: 'bold' }}>Recorded Date</label>
                <input
                  type="date"
                  className="search-input"
                  style={{ width: '100%', marginTop: '4px' }}
                  value={editFormData.recorded_on}
                  onChange={(e) => setEditFormData({ ...editFormData, recorded_on: e.target.value })}
                  required
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '15px' }}>
                <button type="button" onClick={() => setEditingRecord(null)} style={{ padding: '6px 12px', border: '1px solid #ccc', background: '#fff', borderRadius: '4px', cursor: 'pointer' }}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary" style={{ padding: '6px 12px' }}>
                  Save Changes
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};