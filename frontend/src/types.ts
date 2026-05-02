/**
 * Type definitions for the experiment tracker
 */

export interface Experiment {
  id: number;
  name: string;
  base_model: string;
  status: ExperimentStatus;
  dataset_id: number;
  created_at: string;
  hyperparameters: Record<string, string>;
}

export type ExperimentStatus =
  | "queued"
  | "running"
  | "completed"
  | "failed"
  | "cancelled";

export interface ExperimentDetail {
  id: number;
  name: string;
  base_model: string;
  status: ExperimentStatus;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  compute_provider: string | null;
  remote_job_id: string | null;
  compute_config: Record<string, unknown> | null;
  dataset_id: number;
  dataset_name: string;
  file_path: string | null;
  num_samples: number | null;
  hyperparameters: Record<string, string>;
  metric_summary: MetricSummary;
}

export interface MetricSummary {
  total_metrics: number;
  metric_names: string[];
  latest_step: number | null;
}

export interface Dataset {
  id: number;
  name: string;
  file_path: string;
  description: string | null;
  num_samples: number | null;
  created_at: string;
  checksum: string | null;
}

export interface Metric {
  id: number;
  experiment_id: number;
  step: number | null;
  metric_name: string;
  metric_value: number;
  timestamp: string;
}

export interface CreateExperiment {
  name: string;
  base_model: string;
  dataset_id: number;
  hyperparameters: Record<string, string>;
}

export interface CreateDataset {
  name: string;
  description: string;
  file_path: string;
}

export interface WebSocketMessage {
  type: "connected" | "status_update" | "logs" | "metrics" | "error" | "pong";
  experiment_id?: number;
  status?: ExperimentStatus;
  job_id?: string;
  logs?: string;
  metrics?: Record<string, unknown>;
  error?: string;
  timestamp: string;
}

export interface LaunchResponse {
  success: boolean;
  experiment_id: number;
  job_id: string;
  status: string;
}
