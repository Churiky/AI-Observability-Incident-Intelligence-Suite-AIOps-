import React from 'react';
import './IncidentTable.css';

function IncidentTable({ incidents }) {
  if (!incidents || incidents.length === 0) {
    return (
      <div className="incident-table-wrapper empty-state">
        <p>No incidents currently logged.</p>
      </div>
    );
  }

  return (
    <div className="incident-table-wrapper">
      <table className="incident-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Title</th>
            <th>Severity</th>
            <th>Status</th>
            <th>Created At</th>
          </tr>
        </thead>
        <tbody>
          {incidents.map(incident => (
            <tr key={incident.id}>
              <td className="incident-id">#{incident.id}</td>
              <td style={{ fontWeight: 500 }}>{incident.title}</td>
              <td>
                <span className={`badge ${incident.severity.toLowerCase()}`}>
                  {incident.severity}
                </span>
              </td>
              <td>
                <span className={`badge ${incident.status.toLowerCase()}`}>
                  {incident.status}
                </span>
              </td>
              <td style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>
                {new Date(incident.created_at).toLocaleString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default IncidentTable;