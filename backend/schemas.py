from datetime import datetime
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel

from models import PhaseEnum

'''
When you send data from a client to an API, you send 
it as a request body. 
Request Body: data from Client -> API
Response Body: data from API -> Client
To send data: POST, PUT, DELETE, PATCH

declare your data model as a class that inherits from BaseModel
'''


class CreateExperiment(BaseModel):
    name: str
    base_model: str
    dataset_id: int
    hyperparameters: dict[str, str]
    class Config:
        from_attributes = True



class ExperimentResponse(BaseModel):
    id: int                  
    name: str
    base_model: str
    status: str
    dataset_id: int
    created_at: datetime
    hyperparameters:dict[str, str]
    class Config:
        from_attributes = True

class CreateDataset(BaseModel):
    name: str
    description: str
    file_path: str
    ## num_samples and checksum to be calculated after creating dataset
    class Config:
        from_attributes = True

class DatasetResponse(BaseModel):
    id: int
    name: str
    file_path: str
    description: str
    num_samples: int
    created_at: datetime
    checksum: str
    class Config: 
        from_attributes = True

class CreateMetric(BaseModel):
    experiment_id: int
    step: int | None = None
    phase: PhaseEnum
    metric_name: str
    metric_value: float
    class Config:
        from_attributes = True

class MetricResponse(BaseModel):
    id: int
    experiment_id: int
    step: int
    metric_name: str
    metric_value: float
    timestamp: datetime
    class Config:
        from_attributes = True

class HyperparameterDetail(BaseModel):
    param_name: str
    param_value: str
    param_category: str | None
    class Config:
        from_attributes = True

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
    compute_provider:  str | None
    remote_job_id:  str | None
    compute_config:  str | None
    dataset_id: int
    dataset_name: str
    file_path: str | None
    num_samples: int | None
    hyperparameters: List[HyperparameterDetail]
    metric_summary: MetricSummary
    class Config:
        from_attributes = True