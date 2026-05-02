"""
Experiment orchestration service.

This module handles:
- Launching experiments on compute providers
- Monitoring job status
- Updating experiment state in the database
- Broadcasting real-time updates via WebSocket
"""
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Set
from fastapi import WebSocket

from models import Experiment
from providers import get_provider, JobStatus
from database import SessionLocal


class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: Dict[int, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, experiment_id: Optional[int] = None):
        await websocket.accept()
        if experiment_id is not None:
            if experiment_id not in self.active_connections:
                self.active_connections[experiment_id] = set()
            self.active_connections[experiment_id].add(websocket)

    def disconnect(self, websocket: WebSocket, experiment_id: Optional[int] = None):
        if experiment_id is not None and experiment_id in self.active_connections:
            self.active_connections[experiment_id].discard(websocket)
            if not self.active_connections[experiment_id]:
                del self.active_connections[experiment_id]

    async def broadcast_to_experiment(self, experiment_id: int, message: dict):
        if experiment_id in self.active_connections:
            dead_connections = set()
            for connection in self.active_connections[experiment_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    dead_connections.add(connection)

            for conn in dead_connections:
                self.active_connections[experiment_id].discard(conn)

    async def broadcast_to_all(self, message: dict):
        for experiment_connections in self.active_connections.values():
            for connection in experiment_connections:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass


manager = ConnectionManager()


class ExperimentOrchestrator:
    def __init__(self):
        self.running_jobs: Dict[int, asyncio.Task] = {}

    async def launch_experiment(
        self,
        experiment: Experiment,
        db,
        provider_config: Optional[Dict[str, Any]] = None,
    ) -> bool:
        try:
            provider_name = experiment.compute_provider or "local"
            provider = get_provider(provider_name, provider_config)

            dataset = experiment.dataset
            dataset_path = dataset.file_path if dataset else ""

            hyperparameters = {
                hp.param_name: hp.param_value for hp in experiment.hyperparameters
            }

            job_id = await provider.submit_job(
                experiment_id=experiment.id,
                base_model=experiment.base_model,
                dataset_path=dataset_path,
                hyperparameters=hyperparameters,
            )

            experiment.remote_job_id = job_id
            experiment.status = "running"
            experiment.started_at = datetime.now(timezone.utc)
            experiment.compute_config = provider_config

            db.add(experiment)
            db.commit()
            db.refresh(experiment)

            await manager.broadcast_to_experiment(
                experiment.id,
                {
                    "type": "status_update",
                    "experiment_id": experiment.id,
                    "status": "running",
                    "job_id": job_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

            task = asyncio.create_task(
                self._monitor_experiment(
                    experiment.id, job_id, provider_name, provider_config
                )
            )
            self.running_jobs[experiment.id] = task

            return True

        except Exception as e:
            experiment.status = "failed"
            experiment.error_message = str(e)
            experiment.completed_at = datetime.now(timezone.utc)
            db.add(experiment)
            db.commit()

            await manager.broadcast_to_experiment(
                experiment.id,
                {
                    "type": "status_update",
                    "experiment_id": experiment.id,
                    "status": "failed",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )

            return False

    async def _monitor_experiment(
        self,
        experiment_id: int,
        job_id: str,
        provider_name: str,
        provider_config: Optional[Dict[str, Any]],
    ):
        """
        Monitor an experiment's progress and update the database.

        Creates its own DB session to avoid using the request-scoped session
        which may be closed by the time this background task runs.
        """
        provider = get_provider(provider_name, provider_config)
        last_log_position = 0
        db = SessionLocal()

        try:
            while True:
                status = await provider.get_job_status(job_id)

                logs = await provider.get_job_logs(job_id, tail=1000)
                new_logs = logs[last_log_position:]
                last_log_position = len(logs)

                if new_logs:
                    await manager.broadcast_to_experiment(
                        experiment_id,
                        {
                            "type": "logs",
                            "experiment_id": experiment_id,
                            "logs": new_logs,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                    )

                metrics = await provider.get_job_metrics(job_id)
                if metrics:
                    await manager.broadcast_to_experiment(
                        experiment_id,
                        {
                            "type": "metrics",
                            "experiment_id": experiment_id,
                            "metrics": metrics,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                    )

                if status in [
                    JobStatus.COMPLETED,
                    JobStatus.FAILED,
                    JobStatus.CANCELLED,
                ]:
                    experiment = db.get(Experiment, experiment_id)
                    if experiment:
                        experiment.status = status.value
                        experiment.completed_at = datetime.now(timezone.utc)
                        db.add(experiment)
                        db.commit()

                    await manager.broadcast_to_experiment(
                        experiment_id,
                        {
                            "type": "status_update",
                            "experiment_id": experiment_id,
                            "status": status.value,
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        },
                    )

                    if experiment_id in self.running_jobs:
                        del self.running_jobs[experiment_id]

                    break

                await asyncio.sleep(5)

        except Exception as e:
            experiment = db.get(Experiment, experiment_id)
            if experiment:
                experiment.status = "failed"
                experiment.error_message = f"Monitoring error: {str(e)}"
                experiment.completed_at = datetime.now(timezone.utc)
                db.add(experiment)
                db.commit()

            await manager.broadcast_to_experiment(
                experiment_id,
                {
                    "type": "error",
                    "experiment_id": experiment_id,
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                },
            )
        finally:
            db.close()

    async def cancel_experiment(self, experiment_id: int, db) -> bool:
        experiment = db.get(Experiment, experiment_id)
        if not experiment or not experiment.remote_job_id:
            return False

        try:
            provider_name = experiment.compute_provider or "local"
            provider = get_provider(provider_name, experiment.compute_config)

            success = await provider.cancel_job(experiment.remote_job_id)

            if success:
                experiment.status = "cancelled"
                experiment.completed_at = datetime.now(timezone.utc)
                db.add(experiment)
                db.commit()

                await manager.broadcast_to_experiment(
                    experiment_id,
                    {
                        "type": "status_update",
                        "experiment_id": experiment_id,
                        "status": "cancelled",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    },
                )

                if experiment_id in self.running_jobs:
                    self.running_jobs[experiment_id].cancel()
                    del self.running_jobs[experiment_id]

            return success

        except Exception:
            return False


orchestrator = ExperimentOrchestrator()
