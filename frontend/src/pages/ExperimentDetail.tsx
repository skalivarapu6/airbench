import { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import Plot from 'react-plotly.js';
import { getExperiment, getMetrics, createWebSocketConnection, cancelExperiment, launchExperiment } from '../api';
import type { ExperimentDetail as ExperimentDetailType, Metric, WebSocketMessage } from '../types';
import './ExperimentDetail.css';

const ExperimentDetail = () => {
  const { id } = useParams<{ id: string }>();
  const [experiment, setExperiment] = useState<ExperimentDetailType | null>(null);
  const [metrics, setMetrics] = useState<Metric[]>([]);
  const [logs, setLogs] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!id) return;

      try {
        const [expData, metricsData] = await Promise.all([
          getExperiment(parseInt(id)),
          getMetrics(parseInt(id)).catch(() => [])
        ]);

        setExperiment(expData);
        setMetrics(metricsData);
        setError(null);
      } catch (err) {
        setError('Failed to load experiment');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();

    // Set up WebSocket connection
    if (id) {
      const ws = createWebSocketConnection(parseInt(id));
      wsRef.current = ws;

      ws.onmessage = (event) => {
        const message: WebSocketMessage = JSON.parse(event.data);

        if (message.type === 'status_update' && experiment) {
          setExperiment({ ...experiment, status: message.status || experiment.status });
        } else if (message.type === 'logs') {
          setLogs((prev) => prev + (message.logs || ''));
        } else if (message.type === 'metrics') {
          fetchData(); // Refresh data when new metrics arrive
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };

      return () => {
        ws.close();
      };
    }
  }, [id]);

  useEffect(() => {
    // Auto-scroll logs to bottom
    logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const handleCancel = async () => {
    if (!id || !confirm('Are you sure you want to cancel this experiment?')) {
      return;
    }

    try {
      await cancelExperiment(parseInt(id));
    } catch (err) {
      alert('Failed to cancel experiment');
      console.error(err);
    }
  };

  const handleLaunch = async () => {
    if (!id) return;

    try {
      await launchExperiment(parseInt(id));
      const expData = await getExperiment(parseInt(id));
      setExperiment(expData);
    } catch (err) {
      alert('Failed to launch experiment');
      console.error(err);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      queued: '#6c7086',
      running: '#f9e2af',
      completed: '#a6e3a1',
      failed: '#f38ba8',
      cancelled: '#89dceb',
    };
    return colors[status] || '#cdd6f4';
  };

  const renderMetricsChart = () => {
    if (metrics.length === 0) {
      return <p className="no-data">No metrics data yet</p>;
    }

    // Group metrics by metric name
    const metricsByName: Record<string, Metric[]> = {};
    metrics.forEach((m) => {
      if (!metricsByName[m.metric_name]) {
        metricsByName[m.metric_name] = [];
      }
      metricsByName[m.metric_name].push(m);
    });

    const traces = Object.entries(metricsByName).map(([name, data]) => ({
      x: data.map((m) => m.step),
      y: data.map((m) => m.metric_value),
      type: 'scatter' as const,
      mode: 'lines+markers' as const,
      name: name,
      line: { width: 2 },
      marker: { size: 6 },
    }));

    return (
      <Plot
        data={traces}
        layout={{
          title: 'Training Metrics',
          xaxis: { title: 'Step' },
          yaxis: { title: 'Value' },
          paper_bgcolor: '#1e1e2e',
          plot_bgcolor: '#181825',
          font: { color: '#cdd6f4' },
          showlegend: true,
          legend: { orientation: 'h', y: -0.2 },
          margin: { t: 40, b: 80 },
        }}
        style={{ width: '100%', height: '400px' }}
        config={{ responsive: true }}
      />
    );
  };

  if (loading) {
    return <div className="page-container"><p>Loading experiment...</p></div>;
  }

  if (error || !experiment) {
    return <div className="page-container"><p className="error">{error || 'Experiment not found'}</p></div>;
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <div>
          <Link to="/experiments" className="breadcrumb">← Back to Experiments</Link>
          <h1>{experiment.name}</h1>
        </div>
        <div className="header-actions">
          {experiment.status === 'queued' && (
            <button onClick={handleLaunch} className="btn-success">
              Launch Experiment
            </button>
          )}
          {experiment.status === 'running' && (
            <button onClick={handleCancel} className="btn-danger">
              Cancel
            </button>
          )}
        </div>
      </div>

      <div className="detail-grid">
        <div className="detail-section">
          <h2>Overview</h2>
          <div className="info-grid">
            <div className="info-item">
              <span className="label">Status:</span>
              <span className="status-badge" style={{ background: getStatusColor(experiment.status) }}>
                {experiment.status}
              </span>
            </div>
            <div className="info-item">
              <span className="label">Base Model:</span>
              <span className="value">{experiment.base_model}</span>
            </div>
            <div className="info-item">
              <span className="label">Dataset:</span>
              <span className="value">{experiment.dataset_name} ({experiment.num_samples} samples)</span>
            </div>
            <div className="info-item">
              <span className="label">Compute Provider:</span>
              <span className="value">{experiment.compute_provider || 'Not specified'}</span>
            </div>
            <div className="info-item">
              <span className="label">Job ID:</span>
              <span className="value">{experiment.remote_job_id || 'N/A'}</span>
            </div>
            <div className="info-item">
              <span className="label">Created:</span>
              <span className="value">{new Date(experiment.created_at).toLocaleString()}</span>
            </div>
            {experiment.started_at && (
              <div className="info-item">
                <span className="label">Started:</span>
                <span className="value">{new Date(experiment.started_at).toLocaleString()}</span>
              </div>
            )}
            {experiment.completed_at && (
              <div className="info-item">
                <span className="label">Completed:</span>
                <span className="value">{new Date(experiment.completed_at).toLocaleString()}</span>
              </div>
            )}
          </div>
        </div>

        <div className="detail-section">
          <h2>Hyperparameters</h2>
          <div className="hyperparameters-list">
            {experiment.hyperparameters.length > 0 ? (
              experiment.hyperparameters.map((hp, idx) => (
                <div key={idx} className="hyperparameter-item">
                  <span className="param-name">{hp.param_name}:</span>
                  <span className="param-value">{hp.param_value}</span>
                </div>
              ))
            ) : (
              <p className="no-data">No hyperparameters configured</p>
            )}
          </div>
        </div>
      </div>

      <div className="detail-section">
        <h2>Metrics</h2>
        {renderMetricsChart()}
        <div className="metrics-summary">
          <p>Total metrics: {experiment.metric_summary.total_metrics}</p>
          <p>Metric types: {experiment.metric_summary.metric_names.join(', ')}</p>
          {experiment.metric_summary.latest_step !== null && (
            <p>Latest step: {experiment.metric_summary.latest_step}</p>
          )}
        </div>
      </div>

      {experiment.status === 'running' && (
        <div className="detail-section">
          <h2>Live Logs</h2>
          <div className="logs-container">
            <pre className="logs-content">
              {logs || 'Waiting for logs...'}
              <div ref={logsEndRef} />
            </pre>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExperimentDetail;
