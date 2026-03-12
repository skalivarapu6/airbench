"""
Local compute provider - runs training jobs on the same machine or SSH-accessible servers.
"""
import asyncio
import os
import subprocess
from typing import Dict, Any, Optional
from datetime import datetime
from .base import BaseComputeProvider, JobStatus


class LocalProvider(BaseComputeProvider):
    """
    Executes training jobs on the local machine or via SSH.

    This provider is useful for:
    - Development and testing
    - Running on a local GPU machine
    - SSH-accessible remote servers
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.jobs: Dict[str, Dict[str, Any]] = {}  # In-memory job tracking

    def _validate_config(self) -> None:
        """Local provider requires minimal configuration"""
        # Optional: ssh_host, ssh_user, working_dir
        pass

    @property
    def provider_name(self) -> str:
        return "local"

    async def submit_job(
        self,
        experiment_id: int,
        base_model: str,
        dataset_path: str,
        hyperparameters: Dict[str, str],
        script_path: Optional[str] = None
    ) -> str:
        """
        Submit a training job to run locally.

        This creates a subprocess that runs the training script.
        """
        job_id = f"local_{experiment_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Default training script if none provided
        if not script_path:
            script_path = self.config.get("default_script", "train.py")

        # Build command
        working_dir = self.config.get("working_dir", os.getcwd())
        python_path = self.config.get("python_path", "python")

        # Construct command with hyperparameters
        cmd = [
            python_path,
            script_path,
            "--base-model", base_model,
            "--dataset", dataset_path,
            "--experiment-id", str(experiment_id),
        ]

        # Add hyperparameters as command-line args
        for key, value in hyperparameters.items():
            cmd.extend([f"--{key}", value])

        # If SSH is configured, wrap command in SSH
        ssh_host = self.config.get("ssh_host")
        if ssh_host:
            ssh_user = self.config.get("ssh_user", "ubuntu")
            cmd = ["ssh", f"{ssh_user}@{ssh_host}"] + cmd

        # Create log directory
        log_dir = self.config.get("log_dir", "./logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"{job_id}.log")

        # Store job info
        self.jobs[job_id] = {
            "experiment_id": experiment_id,
            "status": JobStatus.QUEUED,
            "command": cmd,
            "log_file": log_file,
            "process": None,
            "submitted_at": datetime.now(),
        }

        # Start the process asynchronously
        asyncio.create_task(self._run_job(job_id))

        return job_id

    async def _run_job(self, job_id: str):
        """Internal method to run the job process"""
        job_info = self.jobs[job_id]
        job_info["status"] = JobStatus.RUNNING

        try:
            # Open log file
            with open(job_info["log_file"], "w") as log_file:
                # Run the process
                process = await asyncio.create_subprocess_exec(
                    *job_info["command"],
                    stdout=log_file,
                    stderr=asyncio.subprocess.STDOUT,
                )
                job_info["process"] = process
                job_info["started_at"] = datetime.now()

                # Wait for completion
                returncode = await process.wait()

                if returncode == 0:
                    job_info["status"] = JobStatus.COMPLETED
                else:
                    job_info["status"] = JobStatus.FAILED
                    job_info["error"] = f"Process exited with code {returncode}"

                job_info["completed_at"] = datetime.now()

        except Exception as e:
            job_info["status"] = JobStatus.FAILED
            job_info["error"] = str(e)
            job_info["completed_at"] = datetime.now()

    async def get_job_status(self, job_id: str) -> JobStatus:
        """Get the current status of a local job"""
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        return self.jobs[job_id]["status"]

    async def get_job_logs(self, job_id: str, tail: int = 100) -> str:
        """Retrieve logs from a job"""
        if job_id not in self.jobs:
            raise ValueError(f"Job {job_id} not found")

        log_file = self.jobs[job_id]["log_file"]

        if not os.path.exists(log_file):
            return ""

        # Read last N lines
        try:
            with open(log_file, "r") as f:
                lines = f.readlines()
                return "".join(lines[-tail:])
        except Exception as e:
            return f"Error reading logs: {str(e)}"

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running local job"""
        if job_id not in self.jobs:
            return False

        job_info = self.jobs[job_id]
        process = job_info.get("process")

        if process and process.returncode is None:
            try:
                process.terminate()
                await asyncio.sleep(2)
                if process.returncode is None:
                    process.kill()
                job_info["status"] = JobStatus.CANCELLED
                job_info["completed_at"] = datetime.now()
                return True
            except Exception:
                return False

        return False

    async def get_job_metrics(self, job_id: str) -> Dict[str, Any]:
        """
        Retrieve metrics from job logs.

        This is a simple implementation that looks for JSON lines in the logs.
        In production, you'd use a proper metrics tracking system.
        """
        logs = await self.get_job_logs(job_id, tail=1000)

        metrics = {}
        # Look for lines like: {"step": 100, "loss": 0.5, "accuracy": 0.95}
        for line in logs.split("\n"):
            if line.strip().startswith("{") and "step" in line:
                try:
                    import json
                    metric = json.loads(line.strip())
                    step = metric.get("step")
                    if step:
                        metrics[f"step_{step}"] = metric
                except:
                    continue

        return metrics

    async def health_check(self) -> bool:
        """Check if local execution is available"""
        try:
            # Check if we can run a simple command
            process = await asyncio.create_subprocess_exec(
                "python", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.wait()
            return process.returncode == 0
        except Exception:
            return False
