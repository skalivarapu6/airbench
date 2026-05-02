import os
from typing import List, Optional

import aiofiles
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_session
from models import Experiment, Metric
from schemas import CreateMetric, MetricResponse

router = APIRouter(prefix="/experiments/{experiment_id}", tags=["metrics"])


@router.post("/metrics", response_model=MetricResponse)
def log_metric(
    experiment_id: int,
    payload: CreateMetric,
    db: Session = Depends(get_session),
):
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    metric = Metric(
        experiment_id=experiment_id,
        step=payload.step,
        phase=payload.phase,
        metric_name=payload.metric_name,
        metric_value=payload.metric_value,
    )
    db.add(metric)
    try:
        db.commit()
    except IntegrityError:
        raise HTTPException(status_code=400, detail="invalid data")
    return metric


@router.get("/metrics", response_model=List[MetricResponse])
def get_metrics(experiment_id: int, db: Session = Depends(get_session)):
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")
    metrics = (
        db.query(Metric)
        .filter(Metric.experiment_id == experiment_id)
        .order_by(Metric.timestamp)
        .all()
    )
    return metrics


@router.get("/logs")
async def get_experiment_logs(
    experiment_id: int,
    tail: Optional[int] = None,
    db: Session = Depends(get_session),
):
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    if experiment.log_file_path is None or not os.path.exists(
        experiment.log_file_path
    ):
        raise HTTPException(status_code=404, detail="No log file found")

    async with aiofiles.open(experiment.log_file_path, mode="r") as f:
        content = await f.read()

    if tail is not None:
        lines = content.splitlines()
        content = "\n".join(lines[-tail:])

    return {"experiment_id": experiment_id, "logs": content}
