import { useEffect, useState } from 'react';
import { getDatasets, createDataset } from '../api';
import type { Dataset } from '../types';
import './DatasetsList.css';

const DatasetsList = () => {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    file_path: '',
  });
  const [formError, setFormError] = useState<string | null>(null);

  const fetchDatasets = async () => {
    try {
      const data = await getDatasets();
      setDatasets(data);
    } catch {
      // Datasets will just be empty
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDatasets();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    try {
      if (!formData.name || !formData.file_path) {
        throw new Error('Name and file path are required');
      }

      await createDataset(formData);
      setFormData({ name: '', description: '', file_path: '' });
      setShowForm(false);
      await fetchDatasets();
    } catch (err: unknown) {
      if (err instanceof Error) {
        setFormError(err.message);
      } else if (
        typeof err === 'object' &&
        err !== null &&
        'response' in err
      ) {
        const axiosErr = err as { response?: { data?: { detail?: string } } };
        setFormError(
          axiosErr.response?.data?.detail || 'Failed to create dataset'
        );
      } else {
        setFormError('Failed to create dataset');
      }
    }
  };

  if (loading) {
    return <div className="page-container"><p>Loading datasets...</p></div>;
  }

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Datasets</h1>
        <button onClick={() => setShowForm(!showForm)} className="btn-primary">
          {showForm ? 'Cancel' : '+ New Dataset'}
        </button>
      </div>

      {showForm && (
        <div className="dataset-form-container">
          {formError && <div className="error-banner">{formError}</div>}
          <form onSubmit={handleSubmit} className="dataset-form">
            <div className="form-group">
              <label htmlFor="name">Dataset Name *</label>
              <input
                type="text"
                id="name"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                placeholder="e.g., instruction-following-v1"
                required
              />
            </div>

            <div className="form-group">
              <label htmlFor="description">Description</label>
              <textarea
                id="description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                placeholder="Brief description of the dataset"
                rows={3}
              />
            </div>

            <div className="form-group">
              <label htmlFor="file_path">File Path *</label>
              <input
                type="text"
                id="file_path"
                value={formData.file_path}
                onChange={(e) => setFormData({ ...formData, file_path: e.target.value })}
                placeholder="/path/to/dataset.json or /path/to/dataset.csv"
                required
              />
              <small className="form-hint">
                Provide the full path to a .json or .csv file on the server
              </small>
            </div>

            <div className="form-actions">
              <button type="button" onClick={() => setShowForm(false)} className="btn-secondary">
                Cancel
              </button>
              <button type="submit" className="btn-primary">
                Create Dataset
              </button>
            </div>
          </form>
        </div>
      )}

      {datasets.length === 0 ? (
        <div className="empty-state">
          <p>No datasets yet</p>
          <button onClick={() => setShowForm(true)} className="btn-primary">
            Create your first dataset
          </button>
        </div>
      ) : (
        <div className="datasets-grid">
          {datasets.map((dataset) => (
            <div key={dataset.id} className="dataset-card">
              <div className="card-header">
                <h3>{dataset.name}</h3>
                <span className="samples-badge">{dataset.num_samples} samples</span>
              </div>

              <div className="card-body">
                <p className="description">{dataset.description || 'No description'}</p>

                <div className="info-row">
                  <span className="label">File:</span>
                  <span className="value file-path">{dataset.file_path}</span>
                </div>

                <div className="info-row">
                  <span className="label">Created:</span>
                  <span className="value">{new Date(dataset.created_at).toLocaleString()}</span>
                </div>

                {dataset.checksum && (
                  <div className="info-row">
                    <span className="label">Checksum:</span>
                    <span className="value checksum">{dataset.checksum.substring(0, 16)}...</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default DatasetsList;
