/**
 * API client for backend communication
 */
import axios from 'axios';
import type {
  Experiment,
  ExperimentDetail,
  Dataset,
  Metric,
  CreateExperiment,
  CreateDataset,
  LaunchResponse,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Experiments
export const getExperiments = async (): Promise<Experiment[]> => {
  const response = await api.get('/experiments');
  return response.data;
};

export const getExperiment = async (id: number): Promise<ExperimentDetail> => {
  const response = await api.get(`/experiments/${id}`);
  return response.data;
};

export const createExperiment = async (data: CreateExperiment): Promise<Experiment> => {
  const response = await api.post('/new_experiment', data);
  return response.data;
};

export const updateExperiment = async (id: number, updates: Record<string, any>): Promise<void> => {
  await api.put(`/experiments/${id}`, updates);
};

export const deleteExperiment = async (id: number): Promise<void> => {
  await api.delete(`/experiments/${id}`);
};

export const launchExperiment = async (
  id: number,
  providerConfig?: Record<string, any>
): Promise<LaunchResponse> => {
  const response = await api.post(`/experiments/${id}/launch`, providerConfig || {});
  return response.data;
};

export const cancelExperiment = async (id: number): Promise<void> => {
  await api.post(`/experiments/${id}/cancel`);
};

// Datasets
export const getDatasets = async (): Promise<Dataset[]> => {
  const response = await api.get('/datasets');
  return response.data;
};

export const createDataset = async (data: CreateDataset): Promise<Dataset> => {
  const response = await api.post('/new_dataset', data);
  return response.data;
};

// Metrics
export const getMetrics = async (experimentId: number): Promise<Metric[]> => {
  const response = await api.get(`/experiments/${experimentId}/metrics`);
  return response.data;
};

export const logMetric = async (
  experimentId: number,
  data: {
    step: number | null;
    phase: "train" | "eval" | "final";
    metric_name: string;
    metric_value: number;
  }
): Promise<Metric> => {
  const response = await api.post(`/experiments/${experimentId}/metrics`, {
    ...data,
    experiment_id: experimentId,
  });
  return response.data;
};

// WebSocket connection helper
export const createWebSocketConnection = (experimentId: number): WebSocket => {
  const wsUrl = API_BASE_URL.replace('http', 'ws');
  return new WebSocket(`${wsUrl}/ws/${experimentId}`);
};

export default api;
