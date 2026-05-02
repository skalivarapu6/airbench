from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_session
from models import Dataset, Experiment, Hyperparameter
from schemas import (
    CreateExperiment,
    ExperimentDetail,
    ExperimentResponse,
    MetricSummary,
    UpdateExperiment,
)
from orchestrator import orchestrator, manager

router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.post("", response_model=ExperimentResponse)
def create_experiment(payload: CreateExperiment, db: Session = Depends(get_session)):
    if db.get(Dataset, payload.dataset_id) is None:
        raise HTTPException(404, "Dataset not found")
    experiment = Experiment(
        name=payload.name,
        base_model=payload.base_model,
        dataset_id=payload.dataset_id,
        status="queued",
    )
    experiment.hyperparameters = [
        Hyperparameter(param_name=k, param_value=v)
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
            hp.param_name: hp.param_value for hp in experiment.hyperparameters
        },
    )


@router.get("", response_model=List[ExperimentResponse])
def list_experiments(
    skip: int = 0, limit: int = 50, db: Session = Depends(get_session)
):
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
                hp.param_name: hp.param_value for hp in exp.hyperparameters
            },
        )
        for exp in experiments
    ]


@router.get("/{experiment_id}", response_model=ExperimentDetail)
def get_experiment(experiment_id: int, db: Session = Depends(get_session)):
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(404, "Experiment not found")

    dataset = db.get(Dataset, experiment.dataset_id)
    if dataset is None:
        raise HTTPException(404, "Dataset not found")

    metrics = experiment.metrics

    return ExperimentDetail(
        id=experiment.id,
        name=experiment.name,
        base_model=experiment.base_model,
        status=experiment.status,
        created_at=experiment.created_at,
        started_at=experiment.started_at,
        completed_at=experiment.completed_at,
        compute_provider=experiment.compute_provider,
        remote_job_id=experiment.remote_job_id,
        compute_config=experiment.compute_config,
        dataset_id=dataset.id,
        dataset_name=dataset.name,
        file_path=dataset.file_path,
        num_samples=dataset.num_samples,
        hyperparameters={
            hp.param_name: hp.param_value for hp in experiment.hyperparameters
        },
        metric_summary=MetricSummary(
            total_metrics=len(metrics),
            metric_names=sorted({m.metric_name for m in metrics}),
            latest_step=max(
                (m.step for m in metrics if m.step is not None), default=None
            ),
        ),
    )


@router.put("/{experiment_id}")
def update_experiment(
    experiment_id: int,
    updates: UpdateExperiment,
    db: Session = Depends(get_session),
):
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(404, "Experiment not found")

    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(experiment, key, value)

    db.add(experiment)
    db.commit()
    db.refresh(experiment)

    return {"success": True, "experiment_id": experiment_id}


@router.delete("/{experiment_id}")
def delete_experiment(experiment_id: int, db: Session = Depends(get_session)):
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(404, "Experiment not found")

    if experiment.status == "running":
        raise HTTPException(
            400, "Cannot delete a running experiment. Cancel it first."
        )

    db.delete(experiment)
    db.commit()

    return {"success": True, "experiment_id": experiment_id}


@router.post("/{experiment_id}/launch")
async def launch_experiment(
    experiment_id: int,
    provider_config: Optional[dict] = None,
    db: Session = Depends(get_session),
):
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(404, "Experiment not found")

    if experiment.status not in ["queued", "failed"]:
        raise HTTPException(
            400,
            f"Cannot launch experiment with status '{experiment.status}'. "
            "Only 'queued' or 'failed' experiments can be launched.",
        )

    success = await orchestrator.launch_experiment(experiment, db, provider_config)

    if not success:
        raise HTTPException(500, "Failed to launch experiment")

    return {
        "success": True,
        "experiment_id": experiment_id,
        "job_id": experiment.remote_job_id,
        "status": experiment.status,
    }


@router.post("/{experiment_id}/cancel")
async def cancel_experiment(
    experiment_id: int, db: Session = Depends(get_session)
):
    experiment = db.get(Experiment, experiment_id)
    if experiment is None:
        raise HTTPException(404, "Experiment not found")

    if experiment.status != "running":
        raise HTTPException(
            400,
            f"Cannot cancel experiment with status '{experiment.status}'. "
            "Only 'running' experiments can be cancelled.",
        )

    success = await orchestrator.cancel_experiment(experiment_id, db)

    if not success:
        raise HTTPException(500, "Failed to cancel experiment")

    return {"success": True, "experiment_id": experiment_id, "status": "cancelled"}
