import React, { useState, useEffect } from 'react';
import '../styles/dashboard.css';
import Card from '../components/Card';
import MetricChart from '../components/MetricChart';
import IncidentTable from '../components/IncidentTable';
import useIncidents from '../hooks/useIncidents';
import useMetrics from '../hooks/useMetrics';
import useWebSocket from '../hooks/useWebSocket';

function Dashboard() {
  const [alerts, setAlerts] = useState([]);
  const { data: incidents, setData: setIncidents, loading: isLoading } = useIncidents();
  const { data: metrics } = useMetrics();

  // WebSocket connection for real-time updates
  const { lastMessage, isConnected } = useWebSocket(['anomaly-alerts', 'incident-updates']);

  // Handle incoming WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      // Add message to live stream panel
      setAlerts(prev => [
        {
          timestamp: new Date().toLocaleTimeString(),
          channel: lastMessage.channel || 'unknown',
          event: lastMessage.event || 'message',
          data: lastMessage.data || lastMessage
        },
        ...prev
      ].slice(0, 15)); // Keep latest 15 alerts in panel

      // Handle real-time updates for incidents list
      if (lastMessage && typeof lastMessage === 'object' && lastMessage.channel === 'incident-updates') {
        const { event, data: incident } = lastMessage;
        if (event === 'incident_created') {
          setIncidents(prev => {
            // Avoid duplicate additions
            if (prev.some(i => i.id === incident.id)) return prev;
            return [incident, ...prev];
          });
        } else if (event === 'incident_updated') {
          setIncidents(prev => prev.map(i => i.id === incident.id ? incident : i));
        }
      }
    }
  }, [lastMessage, setIncidents]);

  // Click handler to trigger mock incident
  const handleSimulateIncident = async () => {
    try {
      const apiHost = window.location.port === '3000' ? 'http://localhost:8000' : '';
      const response = await fetch(`${apiHost}/api/v1/incidents/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title: `Simulated Outage - Service ${String.fromCharCode(65 + Math.floor(Math.random() * 4))}`,
          severity: ['MEDIUM', 'HIGH', 'CRITICAL'][Math.floor(Math.random() * 3)],
          status: 'ACTIVE',
          incident_score: parseFloat((Math.random() * 0.4 + 0.6).toFixed(2)),
          root_cause: 'Simulated memory leakage or CPU threshold spike',
          confidence: parseFloat((Math.random() * 0.2 + 0.75).toFixed(2))
        }),
      });
      if (!response.ok) {
        console.error('Failed to create simulation incident');
      }
    } catch (err) {
      console.error('Error triggering simulation:', err);
    }
  };

  if (isLoading) {
    return (
      <div className="dashboard-loading" style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
        fontFamily: 'var(--font-display)',
        fontSize: '1.2rem',
        color: 'var(--text-muted)'
      }}>
        Initializing AI Observability Engine...
      </div>
    );
  }

  const totalIncidentsCount = incidents.length;
  const activeCount = incidents.filter(i => i.status === 'ACTIVE').length;
  const investigatingCount = incidents.filter(i => i.status === 'INVESTIGATING').length;
  const resolvedCount = incidents.filter(i => i.status === 'RESOLVED').length;

  const incidentSubtext = (
    <>
      <span className="status-indicator active" title="Active">● {activeCount} Act</span>
      <span className="status-indicator investigating" title="Investigating">● {investigatingCount} Inv</span>
      <span className="status-indicator resolved" title="Resolved">● {resolvedCount} Res</span>
    </>
  );

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div className="brand-section">
          <h1>AI Observability Suite</h1>
          <span className="subtitle">Real-time telemetry anomaly monitoring & incident intelligence</span>
        </div>

        <div className="live-indicator-wrapper">
          <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
            <span className="pulse-dot"></span>
            {isConnected ? 'LIVE FEED ACTIVE' : 'DISCONNECTED'}
          </div>

          <button className="btn-simulate" onClick={handleSimulateIncident}>
            <span style={{ fontSize: '1.1rem' }}>⚡</span> Simulate Incident
          </button>
        </div>
      </header>

      <div className="dashboard-grid">
        <main className="main-content-flow">
          <section className="metrics-row">
            <Card 
              title="Total Services" 
              value={metrics?.total_services || 4} 
              type="primary"
            />
            <Card 
              title="System Incidents" 
              value={totalIncidentsCount} 
              type={activeCount > 0 ? 'danger' : 'success'}
              subtext={incidentSubtext}
            />
            <Card 
              title="Anomalies Today" 
              value={metrics?.anomalies_today || 0} 
              type="warning"
            />
            <Card 
              title="Average MTTR" 
              value={metrics?.avg_mttr || 'N/A'} 
              type="success"
            />
          </section>

          <section className="charts-row">
            <MetricChart
              title="System Anomaly Events (24 Hours)"
              metricType="system"
              data={metrics}
            />
            <MetricChart
              title="Incident Occurrence Trend"
              metricType="incidents"
              data={metrics}
            />
          </section>

          <section className="incidents-section">
            <div className="section-header">
              <h2>🚨 System Incidents List ({incidents.length})</h2>
            </div>
            <IncidentTable incidents={incidents} />
          </section>
        </main>

        <aside className="sidebar-flow">
          <div className="terminal-panel">
            <div className="terminal-header">
              <span className="terminal-title">Real-Time Event Stream</span>
              <div className="window-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
            <div className="terminal-content">
              {alerts.length === 0 ? (
                <div className="terminal-empty">
                  No active events.<br/>
                  <span style={{ fontSize: '0.8rem', opacity: 0.5 }}>Waiting for live telemetry metrics or incidents...</span>
                </div>
              ) : (
                alerts.map((alert, index) => (
                  <div key={index} className={`log-entry ${alert.channel}`}>
                    <div className="log-meta">
                      <span className={`log-channel ${alert.channel}`}>
                        [{alert.channel.toUpperCase()}] {alert.event}
                      </span>
                      <span>{alert.timestamp}</span>
                    </div>
                    <pre className="log-body">
                      {JSON.stringify(alert.data, null, 2)}
                    </pre>
                  </div>
                ))
              )}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}

export default Dashboard;