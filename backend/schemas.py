from datetime import datetime
from typing import List
from pydantic import BaseModel, ConfigDict

from models import PhaseEnum


class CreateExperiment(BaseModel):
    name: str
    base_model: str
    dataset_id: int
    hyperparameters: dict[str, str]
    model_config = ConfigDict(from_attributes=True)


class ExperimentResponse(BaseModel):
    id: int
    name: str
    base_model: str
    status: str
    dataset_id: int
    created_at: datetime
    hyperparameters: dict[str, str]
    model_config = ConfigDict(from_attributes=True)


class UpdateExperiment(BaseModel):
    notes: str | None = None
    compute_provider: str | None = None
    compute_config: dict | None = None


class CreateDataset(BaseModel):
    name: str
    description: str
    file_path: str
    model_config = ConfigDict(from_attributes=True)


class DatasetResponse(BaseModel):
    id: int
    name: str
    file_path: str | None
    description: str | None
    num_samples: int | None
    created_at: datetime
    checksum: str | None
    model_config = ConfigDict(from_attributes=True)


class CreateMetric(BaseModel):
    step: int | None = None
    phase: PhaseEnum
    metric_name: str
    metric_value: float
    model_config = ConfigDict(from_attributes=True)


class MetricResponse(BaseModel):
    id: int
    experiment_id: int
    step: int | None
    metric_name: str
    metric_value: float
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)


class MetricSummary(BaseModel):
    total_metrics: int
    metric_names: List[str]
    latest_step: int | None


class ExperimentDetail(BaseModel):
    id: int
    name: str
    base_model: str
    status: str
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    compute_provider: str | None
    remote_job_id: str | None
    compute_config: dict | None
    dataset_id: int
    dataset_name: str
    file_path: str | None
    num_samples: int | None
    hyperparameters: dict[str, str]
    metric_summary: MetricSummary
    model_config = ConfigDict(from_attributes=True)
