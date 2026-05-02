import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { createExperiment, getDatasets } from '../api';
import type { Dataset } from '../types';
import './NewExperiment.css';

const NewExperiment = () => {
  const navigate = useNavigate();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [formData, setFormData] = useState({
    name: '',
    base_model: '',
    dataset_id: '',
    compute_provider: 'local',
  });
  const [hyperparameters, setHyperparameters] = useState<Array<{ name: string; value: string }>>([
    { name: 'learning_rate', value: '2e-5' },
    { name: 'num_epochs', value: '3' },
    { name: 'batch_size', value: '8' },
  ]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDatasets = async () => {
      try {
        const data = await getDatasets();
        setDatasets(data);
      } catch {
        // Datasets will just be empty
      }
    };
    fetchDatasets();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (!formData.name || !formData.base_model || !formData.dataset_id) {
        throw new Error('Please fill in all required fields');
      }

      const hyperparametersObj = hyperparameters.reduce((acc, hp) => {
        if (hp.name && hp.value) {
          acc[hp.name] = hp.value;
        }
        return acc;
      }, {} as Record<string, string>);

      const newExperiment = await createExperiment({
        name: formData.name,
        base_model: formData.base_model,
        dataset_id: parseInt(formData.dataset_id),
        hyperparameters: hyperparametersObj,
      });

      navigate(`/experiments/${newExperiment.id}`);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : 'Failed to create experiment';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const addHyperparameter = () => {
    setHyperparameters([...hyperparameters, { name: '', value: '' }]);
  };

  const removeHyperparameter = (index: number) => {
    setHyperparameters(hyperparameters.filter((_, i) => i !== index));
  };

  const updateHyperparameter = (index: number, field: 'name' | 'value', value: string) => {
    const updated = [...hyperparameters];
    updated[index][field] = value;
    setHyperparameters(updated);
  };

  return (
    <div className="page-container">
      <div className="page-header">
        <h1>Create New Experiment</h1>
      </div>

      {error && <div className="error-banner">{error}</div>}

      <form onSubmit={handleSubmit} className="experiment-form">
        <div className="form-section">
          <h2>Basic Information</h2>

          <div className="form-group">
            <label htmlFor="name">Experiment Name *</label>
            <input
              type="text"
              id="name"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="e.g., llama2-fine-tune-v1"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="base_model">Base Model *</label>
            <input
              type="text"
              id="base_model"
              value={formData.base_model}
              onChange={(e) => setFormData({ ...formData, base_model: e.target.value })}
              placeholder="e.g., meta-llama/Llama-2-7b-hf"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="dataset_id">Dataset *</label>
            <select
              id="dataset_id"
              value={formData.dataset_id}
              onChange={(e) => setFormData({ ...formData, dataset_id: e.target.value })}
              required
            >
              <option value="">Select a dataset</option>
              {datasets.map((dataset) => (
                <option key={dataset.id} value={dataset.id}>
                  {dataset.name} ({dataset.num_samples} samples)
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="compute_provider">Compute Provider</label>
            <select
              id="compute_provider"
              value={formData.compute_provider}
              onChange={(e) => setFormData({ ...formData, compute_provider: e.target.value })}
            >
              <option value="local">Local</option>
              <option value="runpod">RunPod</option>
              <option value="lambda">Lambda Labs</option>
              <option value="modal">Modal</option>
            </select>
          </div>
        </div>

        <div className="form-section">
          <div className="section-header">
            <h2>Hyperparameters</h2>
            <button type="button" onClick={addHyperparameter} className="btn-secondary">
              + Add Parameter
            </button>
          </div>

          <div className="hyperparameters-form">
            {hyperparameters.map((hp, index) => (
              <div key={index} className="hyperparameter-row">
                <input
                  type="text"
                  placeholder="Parameter name"
                  value={hp.name}
                  onChange={(e) => updateHyperparameter(index, 'name', e.target.value)}
                />
                <input
                  type="text"
                  placeholder="Value"
                  value={hp.value}
                  onChange={(e) => updateHyperparameter(index, 'value', e.target.value)}
                />
                <button
                  type="button"
                  onClick={() => removeHyperparameter(index)}
                  className="btn-danger-small"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="form-actions">
          <button
            type="button"
            onClick={() => navigate('/experiments')}
            className="btn-secondary"
            disabled={loading}
          >
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={loading}>
            {loading ? 'Creating...' : 'Create Experiment'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default NewExperiment;
