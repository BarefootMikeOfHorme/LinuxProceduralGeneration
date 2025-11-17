/**
 * VaultMind Forge - LineageViewer React Component
 *
 * Interactive lineage record viewer with filtering, sorting, and statistics
 * Three view modes: Grid, List, Timeline
 */

import React, { useState, useEffect, useMemo } from 'react';
import './LineageViewer.css';

const LineageViewer = ({ apiBaseUrl = 'http://localhost:3000/api' }) => {
  // State
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [viewMode, setViewMode] = useState('grid'); // grid, list, timeline
  const [filters, setFilters] = useState({
    search: '',
    jobId: '',
    branch: '',
    status: ''
  });
  const [sortBy, setSortBy] = useState('timestamp');
  const [sortOrder, setSortOrder] = useState('desc');

  // Fetch lineage records
  useEffect(() => {
    fetchRecords();
  }, [filters.jobId, filters.branch, filters.status]);

  const fetchRecords = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (filters.jobId) params.append('jobId', filters.jobId);
      if (filters.branch) params.append('branch', filters.branch);
      if (filters.status) params.append('status', filters.status);

      const response = await fetch(`${apiBaseUrl}/lineage?${params}`);
      const data = await response.json();

      if (data.success) {
        setRecords(data.data.records || []);
      } else {
        setError(data.message || 'Failed to fetch records');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Filter and sort records
  const filteredRecords = useMemo(() => {
    let filtered = [...records];

    // Search filter
    if (filters.search) {
      const search = filters.search.toLowerCase();
      filtered = filtered.filter(record =>
        record.run_id?.toLowerCase().includes(search) ||
        record.lineage?.job_id?.toLowerCase().includes(search)
      );
    }

    // Sort
    filtered.sort((a, b) => {
      let aVal, bVal;

      switch (sortBy) {
        case 'timestamp':
          aVal = new Date(a.timestamp);
          bVal = new Date(b.timestamp);
          break;
        case 'jobId':
          aVal = a.lineage?.job_id || '';
          bVal = b.lineage?.job_id || '';
          break;
        case 'score':
          aVal = calculateAvgScore(a);
          bVal = calculateAvgScore(b);
          break;
        case 'duration':
          aVal = a.execution?.duration_ms || 0;
          bVal = b.execution?.duration_ms || 0;
          break;
        default:
          aVal = a.timestamp;
          bVal = b.timestamp;
      }

      if (sortOrder === 'asc') {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });

    return filtered;
  }, [records, filters.search, sortBy, sortOrder]);

  // Calculate statistics
  const stats = useMemo(() => {
    const total = records.length;
    const completed = records.filter(r => r.execution?.status === 'completed').length;
    const failed = records.filter(r => r.execution?.status === 'failed').length;
    const totalAssets = records.reduce((sum, r) => sum + (r.assets?.length || 0), 0);
    const avgScore = records.reduce((sum, r) => sum + calculateAvgScore(r), 0) / (total || 1);
    const avgDuration = records.reduce((sum, r) => sum + (r.execution?.duration_ms || 0), 0) / (total || 1);

    return {
      total,
      completed,
      failed,
      totalAssets,
      avgScore: avgScore.toFixed(3),
      avgDuration: formatDuration(avgDuration)
    };
  }, [records]);

  // Helper functions
  const calculateAvgScore = (record) => {
    if (!record.validations || record.validations.length === 0) return 0;
    const sum = record.validations.reduce((s, v) => s + (v.score || 0), 0);
    return sum / record.validations.length;
  };

  const formatDuration = (ms) => {
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(2)}s`;
    return `${(ms / 60000).toFixed(2)}m`;
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp).toLocaleString();
  };

  // Render functions
  const renderFilters = () => (
    <div className="lineage-filters">
      <input
        type="text"
        placeholder="Search run ID or job ID..."
        value={filters.search}
        onChange={(e) => setFilters({ ...filters, search: e.target.value })}
        className="filter-search"
      />
      <input
        type="text"
        placeholder="Job ID"
        value={filters.jobId}
        onChange={(e) => setFilters({ ...filters, jobId: e.target.value })}
        className="filter-input"
      />
      <input
        type="text"
        placeholder="Branch"
        value={filters.branch}
        onChange={(e) => setFilters({ ...filters, branch: e.target.value })}
        className="filter-input"
      />
      <select
        value={filters.status}
        onChange={(e) => setFilters({ ...filters, status: e.target.value })}
        className="filter-select"
      >
        <option value="">All Status</option>
        <option value="completed">Completed</option>
        <option value="failed">Failed</option>
        <option value="running">Running</option>
      </select>
      <button onClick={fetchRecords} className="btn-refresh">Refresh</button>
    </div>
  );

  const renderStats = () => (
    <div className="lineage-stats">
      <div className="stat-card">
        <div className="stat-value">{stats.total}</div>
        <div className="stat-label">Total Runs</div>
      </div>
      <div className="stat-card">
        <div className="stat-value">{stats.completed}</div>
        <div className="stat-label">Completed</div>
      </div>
      <div className="stat-card">
        <div className="stat-value">{stats.failed}</div>
        <div className="stat-label">Failed</div>
      </div>
      <div className="stat-card">
        <div className="stat-value">{stats.totalAssets}</div>
        <div className="stat-label">Total Assets</div>
      </div>
      <div className="stat-card">
        <div className="stat-value">{stats.avgScore}</div>
        <div className="stat-label">Avg Score</div>
      </div>
      <div className="stat-card">
        <div className="stat-value">{stats.avgDuration}</div>
        <div className="stat-label">Avg Duration</div>
      </div>
    </div>
  );

  const renderGridView = () => (
    <div className="lineage-grid">
      {filteredRecords.map(record => (
        <div key={record.run_id} className={`lineage-card status-${record.execution?.status}`}>
          <div className="card-header">
            <div className="card-title">{record.lineage?.job_id}</div>
            <div className={`card-status status-${record.execution?.status}`}>
              {record.execution?.status}
            </div>
          </div>
          <div className="card-body">
            <div className="card-info">
              <span className="info-label">Run ID:</span>
              <span className="info-value">{record.run_id.substring(0, 12)}...</span>
            </div>
            <div className="card-info">
              <span className="info-label">Branch:</span>
              <span className="info-value">{record.lineage?.branch}</span>
            </div>
            <div className="card-info">
              <span className="info-label">Assets:</span>
              <span className="info-value">{record.assets?.length || 0}</span>
            </div>
            <div className="card-info">
              <span className="info-label">Score:</span>
              <span className="info-value">{calculateAvgScore(record).toFixed(3)}</span>
            </div>
            <div className="card-info">
              <span className="info-label">Duration:</span>
              <span className="info-value">{formatDuration(record.execution?.duration_ms || 0)}</span>
            </div>
            <div className="card-info">
              <span className="info-label">Time:</span>
              <span className="info-value">{formatTimestamp(record.timestamp)}</span>
            </div>
          </div>
          {record.rejections && record.rejections.length > 0 && (
            <div className="card-rejections">
              <div className="rejections-label">Rejections: {record.rejections.length}</div>
            </div>
          )}
        </div>
      ))}
    </div>
  );

  const renderListView = () => (
    <div className="lineage-list">
      <table className="lineage-table">
        <thead>
          <tr>
            <th onClick={() => handleSort('timestamp')}>Timestamp</th>
            <th onClick={() => handleSort('jobId')}>Job ID</th>
            <th>Run ID</th>
            <th>Branch</th>
            <th>Status</th>
            <th onClick={() => handleSort('score')}>Avg Score</th>
            <th>Assets</th>
            <th onClick={() => handleSort('duration')}>Duration</th>
          </tr>
        </thead>
        <tbody>
          {filteredRecords.map(record => (
            <tr key={record.run_id} className={`row-${record.execution?.status}`}>
              <td>{formatTimestamp(record.timestamp)}</td>
              <td>{record.lineage?.job_id}</td>
              <td title={record.run_id}>{record.run_id.substring(0, 12)}...</td>
              <td>{record.lineage?.branch}</td>
              <td><span className={`badge badge-${record.execution?.status}`}>{record.execution?.status}</span></td>
              <td>{calculateAvgScore(record).toFixed(3)}</td>
              <td>{record.assets?.length || 0}</td>
              <td>{formatDuration(record.execution?.duration_ms || 0)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );

  const renderTimelineView = () => (
    <div className="lineage-timeline">
      {filteredRecords.map((record, index) => (
        <div key={record.run_id} className="timeline-item">
          <div className="timeline-marker"></div>
          <div className="timeline-content">
            <div className="timeline-header">
              <span className="timeline-time">{formatTimestamp(record.timestamp)}</span>
              <span className={`timeline-status status-${record.execution?.status}`}>
                {record.execution?.status}
              </span>
            </div>
            <div className="timeline-body">
              <div className="timeline-title">{record.lineage?.job_id}</div>
              <div className="timeline-details">
                Run: {record.run_id.substring(0, 12)}... |
                Branch: {record.lineage?.branch} |
                Assets: {record.assets?.length || 0} |
                Score: {calculateAvgScore(record).toFixed(3)}
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );

  const handleSort = (column) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  // Main render
  return (
    <div className="lineage-viewer">
      <div className="lineage-header">
        <h1>🧬 Lineage Viewer</h1>
        <div className="view-mode-selector">
          <button
            className={`btn-view-mode ${viewMode === 'grid' ? 'active' : ''}`}
            onClick={() => setViewMode('grid')}
          >
            Grid
          </button>
          <button
            className={`btn-view-mode ${viewMode === 'list' ? 'active' : ''}`}
            onClick={() => setViewMode('list')}
          >
            List
          </button>
          <button
            className={`btn-view-mode ${viewMode === 'timeline' ? 'active' : ''}`}
            onClick={() => setViewMode('timeline')}
          >
            Timeline
          </button>
        </div>
      </div>

      {renderFilters()}
      {renderStats()}

      {loading && <div className="loading">Loading lineage records...</div>}
      {error && <div className="error">Error: {error}</div>}

      {!loading && !error && (
        <>
          {filteredRecords.length === 0 ? (
            <div className="empty-state">
              <p>No lineage records found</p>
              <p className="empty-hint">Generate some assets to see lineage tracking in action</p>
            </div>
          ) : (
            <>
              {viewMode === 'grid' && renderGridView()}
              {viewMode === 'list' && renderListView()}
              {viewMode === 'timeline' && renderTimelineView()}
            </>
          )}
        </>
      )}
    </div>
  );
};

export default LineageViewer;
