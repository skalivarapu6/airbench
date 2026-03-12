import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getExperiments, deleteExperiment, launchExperiment } from '../api';
import type { Experiment } from '../types';
import './ExperimentsList.css';

const ExperimentsList = () => {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchExperiments = async () => {
    try {
      const data = await getExperiments();
      setExperiments(data);
      setError(null);
    } catch (err) {
      setError('Failed to load experiments');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExperiments();
    // Poll for updates every 5 seconds
    const interval = setInterval(fetchExperiments, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this experiment?')) {
      return;
    }

    try {
      await deleteExperiment(id);
      setExperiments(experiments.filter(exp => exp.id !== id));
    } catch (err) {
      alert('Failed to delete experiment');
      console.error(err);
    }
  };

  const handleLaunch = async (id: number) => {
    try {
      await launchExperiment(id);
      await fetchExperiments();
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

  if (loading) {
    return <div className="page-container"><p>Loading experiments...</p></div>;
  }

  if (error) {
    return <div className="page-container"><p className="error">{error}</p></div>;
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Experiments</h1>
        <Link to="/experiments/new" className="btn-primary">
          + New Experiment
        </Link>
      </div>

      {experiments.length === 0 ? (
        <div className="empty-state">
          <p>No experiments yet</p>
          <Link to="/experiments/new">Create your first experiment</Link>
        </div>
      ) : (
        <div className="experiments-grid">
          {experiments.map((exp) => (
            <div key={exp.id} className="experiment-card">
              <div className="card-header">
                <Link to={`/experiments/${exp.id}`}>
                  <h3>{exp.name}</h3>
                </Link>
                <span
                  className="status-badge"
                  style={{ background: getStatusColor(exp.status) }}
                >
                  {exp.status}
                </span>
              </div>

              <div className="card-body">
                <div className="info-row">
                  <span className="label">Model:</span>
                  <span className="value">{exp.base_model}</span>
                </div>
                <div className="info-row">
                  <span className="label">Created:</span>
                  <span className="value">
                    {new Date(exp.created_at).toLocaleString()}
                  </span>
                </div>
                <div className="info-row">
                  <span className="label">Hyperparameters:</span>
                  <span className="value">
                    {Object.keys(exp.hyperparameters).length} params
                  </span>
                </div>
              </div>

              <div className="card-actions">
                <Link to={`/experiments/${exp.id}`} className="btn-secondary">
                  View Details
                </Link>
                {exp.status === 'queued' && (
                  <button
                    onClick={() => handleLaunch(exp.id)}
                    className="btn-success"
                  >
                    Launch
                  </button>
                )}
                {exp.status !== 'running' && (
                  <button
                    onClick={() => handleDelete(exp.id)}
                    className="btn-danger"
                  >
                    Delete
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ExperimentsList;
