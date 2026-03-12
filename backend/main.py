import csv
import hashlib
import json
import os
import aiofiles
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session
from models import Dataset, Experiment, Hyperparameter, Metric
from database import init_db, get_session
from schemas import CreateDataset, CreateExperiment, CreateMetric, DatasetResponse, ExperimentDetail, ExperimentResponse, MetricResponse, MetricSummary
from orchestrator import orchestrator, manager

app = FastAPI()

# Add CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()


@app.post("/new_experiment", response_model=ExperimentResponse)
async def new_experiment(payload: CreateExperiment, db: Session = Depends(get_session)) :
    # add and update data to database(here you split the payload to experiments 
    # and hyperparam classes
    if db.get(Dataset, payload.dataset_id) is None:
        raise HTTPException(404, "Dataset not found")
    experiment = Experiment(
        name = payload.name,
        base_model = payload.base_model,
        dataset_id = payload.dataset_id,
        status = "queued",
    )
    experiment.hyperparameters = [
        Hyperparameter(
        param_name=k,
        param_value=v,
        )
        for k, v in payload.hyperparameters.items()
    ]

    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return ExperimentResponse(
        id=experiment.id,
        name=experiment.name,
        base_model=experiment.base_model,
        status=experiment.status,
        dataset_id=experiment.dataset_id,
        created_at=experiment.created_at,
        hyperparameters={
            hp.param_name: hp.param_value
            for hp in experiment.hyperparameters
        }
    )

@app.get("/experiments", response_model=List[ExperimentResponse])
async def get_experiments(skip: int = 0, limit: int = 50, db: Session = Depends(get_session)):
    experiments = db.query(Experiment).offset(skip).limit(limit).all()
    return [
        ExperimentResponse(
            id=exp.id,
            name=exp.name,
            base_model=exp.base_model,
            status=exp.status,
            dataset_id=exp.dataset_id,
            created_at=exp.created_at,
            hyperparameters={
                hp.param_name: hp.param_value
                for hp in exp.hyperparameters
            }
        )
        for exp in experiments
    ]

@app.post("/new_dataset", response_model=DatasetResponse)
async def new_dataset(payload: CreateDataset, db: Session = Depends(get_session)):
    data = Dataset(
        name  = payload.name,
        description = payload.description,
        file_path = payload.file_path,
    )
    if not os.path.exists(payload.file_path):
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )
    if not payload.file_path.endswith((".json", ".csv")):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format (only .json or .csv allowed)"
        )
    try:
        async with aiofiles.open(payload.file_path, mode="rb") as f:
            content_bytes = await f.read()
        data.checksum = hashlib.sha256(content_bytes).hexdigest()
        content = content_bytes.decode("utf-8")

        if payload.file_path.endswith(".json"):
            parsed = json.loads(content)
            data.num_samples = len(parsed)
        elif payload.file_path.endswith(".csv"):
            reader = csv.reader(content.splitlines())
            data.num_samples = sum(1 for _ in reader) - 1

    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON file"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to process dataset file: {str(e)}"
        )
    db.add(data)
    db.commit()
    db.refresh(data)
    return data

@app.get("/datasets", response_model=List[DatasetResponse])
async def get_datasets(skip: int = 0, limit: int = 50, db: Session = Depends(get_session)):
    datasets = db.query(Dataset).offset(skip).limit(limit).all()
    return [
        DatasetResponse(
            id = dataset.id,
            name = dataset.name,
            file_path = dataset.file_path,
            num_samples= dataset.num_samples,
            created_at = dataset.created_at,
            checksum = dataset.checksum,
        )
        for dataset in datasets
    ]

@app.get("/datasets/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(dataset_id: int, db: Session = Depends(get_session)):
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(404, "Dataset not found")
    return DatasetResponse(
        id=dataset.id,
        name=dataset.name,
        file_path=dataset.file_path,
        description=dataset.description,
        num_samples=dataset.num_samples,
        created_at=dataset.created_at,
        checksum=dataset.checksum,
    )

@app.delete("/datasets/{dataset_id}")
async def delete_dataset(dataset_id: int, db: Session = Depends(get_session)):
    dataset = db.get(Dataset, dataset_id)
    if dataset is None:
        raise HTTPException(404, "Dataset not found")
    experiments = db.query(Experiment).filter(Experiment.dataset_id == dataset_id).first()
    if experiments is not None:
        raise HTTPException(400, "Cannot delete dataset that is referenced by experiments.")
    db.delete(dataset)
    db.commit()
    return {"success": True, "dataset_id": dataset_id}

@app.post("/experiments/{experiment_id}/metrics", response_model=MetricResponse)
async def log_metric(
        experiment_id: int,
        payload: CreateMetric,
        db: Session = Depends(get_session)
):
    payload.experiment_id = experiment_id
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found"
        )
    metric = Metric(
        experiment_id = experiment_id,
        step = payload.step,
        phase = payload.phase,
        metric_name = payload.metric_name,
        metric_value = payload.metric_value
    )
    db.add(metric)
    try:
        db.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail='invalid data'
        )
    return metric
    
@app.get("/experiments/{experiment_id}/metrics", response_model=List[MetricResponse])
async def get_metrics(experiment_id: int, db: Session = Depends(get_session)):
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="Experiment not found"
        )
    metrics = (
        db.query(Metric)
        .filter(Metric.experiment_id == experiment_id)
        .order_by(Metric.timestamp)
        .all()
    )
    return metrics

@app.get("/experiments/{experiment_id}/logs")
async def get_experiment_logs(
    experiment_id: int,
    tail: Optional[int] = None,
    db: Session = Depends(get_session),
):
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if experiment.log_file_path is None or not os.path.exists(experiment.log_file_path):
        raise HTTPException(status_code=404, detail="No log file found")

    async with aiofiles.open(experiment.log_file_path, mode="r") as f:
        content = await f.read()

    if tail is not None:
        lines = content.splitlines()
        content = "\n".join(lines[-tail:])

    return {"experiment_id": experiment_id, "logs": content}

@app.get("/experiments/{experiment_id}", response_model=ExperimentDetail)
async def experiment_detail(experiment_id: int, db: Session = Depends(get_session)):
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(404, "Experiment not found")

    dataset = db.get(Dataset, experiment.dataset_id)
    if dataset is None:
        raise HTTPException(404, "Dataset not found")

    hyperparameters = experiment.hyperparameters
    metrics = experiment.metrics
    # MetricSummary = {
    # "total_entries": len(metrics),
    # "metric_names": sorted({m.metric_name for m in metrics}),
    # "latest_step": max((m.step for m in metrics if m.step is not None), default=None),
    # }


    response = ExperimentDetail(
        id= experiment.id,
        name = experiment.name,
        base_model = experiment.base_model,
        status = experiment.status,
        created_at = experiment.created_at,
        started_at = experiment.started_at,
        completed_at = experiment.completed_at,
        compute_provider=  experiment.compute_provider,
        remote_job_id=  experiment.remote_job_id,
        compute_config=  experiment.compute_config,
        dataset_id = dataset.id,
        dataset_name = dataset.name,
        file_path = dataset.file_path,
        num_samples = dataset.num_samples,
        hyperparameters = hyperparameters,
        metric_summary=MetricSummary(
            total_metrics=len(metrics),
            metric_names= sorted({m.metric_name for m in metrics}),
            latest_step =  max((m.step for m in metrics if m.step is not None), default=None),
        )
    )
    return response


# WebSocket endpoint for real-time updates
@app.websocket("/ws/{experiment_id}")
async def websocket_endpoint(websocket: WebSocket, experiment_id: int):
    """
    WebSocket endpoint for real-time experiment updates.

    Clients connect to receive:
    - Status updates
    - Log streams
    - Metrics updates
    """
    await manager.connect(websocket, experiment_id)
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "experiment_id": experiment_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

        # Keep connection alive and listen for client messages
        while True:
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_json({
                "type": "pong",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket, experiment_id)


# Launch experiment endpoint
@app.post("/experiments/{experiment_id}/launch")
async def launch_experiment(
    experiment_id: int,
    provider_config: Optional[dict] = None,
    db: Session = Depends(get_session)
):
    """
    Launch an experiment on the configured compute provider.

    Args:
        experiment_id: ID of the experiment to launch
        provider_config: Optional provider-specific configuration
    """
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(404, "Experiment not found")

    if experiment.status not in ["queued", "failed"]:
        raise HTTPException(
            400,
            f"Cannot launch experiment with status '{experiment.status}'. "
            "Only 'queued' or 'failed' experiments can be launched."
        )

    success = await orchestrator.launch_experiment(experiment, db, provider_config)

    if not success:
        raise HTTPException(500, "Failed to launch experiment")

    return {
        "success": True,
        "experiment_id": experiment_id,
        "job_id": experiment.remote_job_id,
        "status": experiment.status
    }


# Cancel experiment endpoint
@app.post("/experiments/{experiment_id}/cancel")
async def cancel_experiment(
    experiment_id: int,
    db: Session = Depends(get_session)
):
    """Cancel a running experiment"""
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(404, "Experiment not found")

    if experiment.status != "running":
        raise HTTPException(
            400,
            f"Cannot cancel experiment with status '{experiment.status}'. "
            "Only 'running' experiments can be cancelled."
        )

    success = await orchestrator.cancel_experiment(experiment_id, db)

    if not success:
        raise HTTPException(500, "Failed to cancel experiment")

    return {
        "success": True,
        "experiment_id": experiment_id,
        "status": "cancelled"
    }


# Update experiment endpoint
@app.put("/experiments/{experiment_id}")
async def update_experiment(
    experiment_id: int,
    updates: dict,
    db: Session = Depends(get_session)
):
    """Update experiment fields (notes, compute_provider, etc.)"""
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(404, "Experiment not found")

    # Only allow updating certain fields
    allowed_fields = {"notes", "compute_provider", "compute_config"}
    for key, value in updates.items():
        if key in allowed_fields:
            setattr(experiment, key, value)

    db.add(experiment)
    db.commit()
    db.refresh(experiment)

    return {"success": True, "experiment_id": experiment_id}


# Delete experiment endpoint
@app.delete("/experiments/{experiment_id}")
async def delete_experiment(
    experiment_id: int,
    db: Session = Depends(get_session)
):
    """Delete an experiment (must not be running)"""
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(404, "Experiment not found")

    if experiment.status == "running":
        raise HTTPException(
            400,
            "Cannot delete a running experiment. Cancel it first."
        )

    db.delete(experiment)
    db.commit()

    return {"success": True, "experiment_id": experiment_id}