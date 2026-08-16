import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid
} from 'recharts';
import './MetricChart.css';

function MetricChart({ title, metricType, data }) {
  const renderChart = () => {
    if (!data) return <div className="chart-fallback">Loading metrics...</div>;

    if (metricType === 'system') {
      const hourlyData = data.hourly_anomalies
        ? data.hourly_anomalies.map((val, idx) => ({ hour: `${idx}h`, anomalies: val }))
        : [];

      if (hourlyData.length === 0) {
        return <div className="chart-fallback">No anomaly trend data available</div>;
      }

      return (
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={hourlyData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="colorAnomalies" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--color-info)" stopOpacity={0.4}/>
                <stop offset="95%" stopColor="var(--color-info)" stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
            <XAxis 
              dataKey="hour" 
              stroke="var(--text-muted)" 
              fontSize={11} 
              tickLine={false} 
            />
            <YAxis 
              stroke="var(--text-muted)" 
              fontSize={11} 
              tickLine={false} 
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                background: 'var(--bg-main)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                color: 'var(--text-main)',
                fontFamily: 'var(--font-display)'
              }}
            />
            <Area
              type="monotone"
              dataKey="anomalies"
              stroke="var(--color-info)"
              strokeWidth={2}
              fillOpacity={1}
              fill="url(#colorAnomalies)"
            />
          </AreaChart>
        </ResponsiveContainer>
      );
    }

    if (metricType === 'incidents') {
      const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
      const trendData = data.incident_trend
        ? data.incident_trend.map((val, idx) => ({ day: days[idx] || `D${idx}`, incidents: val }))
        : [];

      if (trendData.length === 0) {
        return <div className="chart-fallback">No incident trend data available</div>;
      }

      return (
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={trendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255, 255, 255, 0.05)" />
            <XAxis 
              dataKey="day" 
              stroke="var(--text-muted)" 
              fontSize={11} 
              tickLine={false} 
            />
            <YAxis 
              stroke="var(--text-muted)" 
              fontSize={11} 
              tickLine={false} 
              axisLine={false}
            />
            <Tooltip
              contentStyle={{
                background: 'var(--bg-main)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                color: 'var(--text-main)',
                fontFamily: 'var(--font-display)'
              }}
            />
            <Bar 
              dataKey="incidents" 
              fill="var(--color-primary)" 
              radius={[4, 4, 0, 0]}
              maxBarSize={40}
            />
          </BarChart>
        </ResponsiveContainer>
      );
    }

    return <div className="chart-fallback">Unknown chart type</div>;
  };

  return (
    <div className="metric-chart">
      <h3>{title}</h3>
      <div className="chart-container-inner">
        {renderChart()}
      </div>
    </div>
  );
}

export default MetricChart;