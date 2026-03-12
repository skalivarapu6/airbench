"""
Modal compute provider integration.

Modal is a modern serverless platform with excellent Python integration.
Docs: https://modal.com/docs
"""
import logging
from typing import Dict, Any, Optional
from .base import BaseComputeProvider, JobStatus

logger = logging.getLogger(__name__)


class ModalProvider(BaseComputeProvider):
    """
    Modal provider for serverless Python execution.

    Configuration required:
    - token_id: Modal token ID
    - token_secret: Modal token secret
    - gpu: (optional) GPU type (e.g., 'a100', 't4', 'any')
    """

    def _validate_config(self) -> None:
        """Validate Modal configuration"""
        if "token_id" not in self.config or "token_secret" not in self.config:
            raise ValueError("Modal token_id and token_secret are required in config.")

    @property
    def provider_name(self) -> str:
        return "modal"

    async def submit_job(
        self,
        experiment_id: int,
        base_model: str,
        dataset_path: str,
        hyperparameters: Dict[str, str],
        script_path: Optional[str] = None
    ) -> str:
        """
        Submit a job to Modal.

        TODO: Implement Modal SDK integration.
        Modal uses a different paradigm - you define functions with decorators.

        Example Modal app structure:

        ```python
        import modal

        stub = modal.Stub("training-job")

        @stub.function(
            gpu="a100",
            timeout=3600,
            image=modal.Image.debian_slim().pip_install(["torch", "transformers"])
        )
        def train_model(experiment_id, base_model, dataset_path, hyperparameters):
            # Training code here
            pass

        # Submit job
        call = train_model.spawn(experiment_id, base_model, dataset_path, hyperparameters)
        return call.object_id
        ```
        """
        # TEMPLATE IMPLEMENTATION

        token_id = self.config["token_id"]
        token_secret = self.config["token_secret"]
        gpu = self.config.get("gpu", "any")

        # Example pseudo-code for Modal:
        # import modal
        #
        # # Set credentials
        # modal.config.set_credentials(token_id, token_secret)
        #
        # # Create or load training app
        # stub = modal.Stub.lookup("training-app", create_if_missing=True)
        #
        # # Submit function call
        # call = stub.train.spawn(
        #     experiment_id=experiment_id,
        #     base_model=base_model,
        #     dataset_path=dataset_path,
        #     hyperparameters=hyperparameters
        # )
        #
        # return call.object_id

        job_id = f"modal_{experiment_id}"
        logger.warning("Modal provider is a stub — returning mock job ID %s", job_id)
        return job_id

    async def get_job_status(self, job_id: str) -> JobStatus:
        """
        Get job status from Modal.

        TODO: Query Modal function call status
        """
        # Example:
        # import modal
        # call = modal.FunctionCall.from_id(job_id)
        #
        # if call.is_finished():
        #     if call.exception:
        #         return JobStatus.FAILED
        #     return JobStatus.COMPLETED
        # return JobStatus.RUNNING

        return JobStatus.QUEUED

    async def get_job_logs(self, job_id: str, tail: int = 100) -> str:
        """
        Retrieve logs from Modal function.

        TODO: Get function call logs
        """
        # Example:
        # import modal
        # call = modal.FunctionCall.from_id(job_id)
        # logs = call.get_logs(tail=tail)
        # return "\n".join(logs)

        return f"[Modal] Logs for {job_id} (not implemented)"

    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a Modal function call.

        TODO: Cancel the running function
        """
        # Example:
        # import modal
        # call = modal.FunctionCall.from_id(job_id)
        # call.cancel()
        # return True

        return False

    async def get_job_metrics(self, job_id: str) -> Dict[str, Any]:
        """
        Retrieve metrics from Modal job.

        TODO: Parse function logs or use custom metrics storage
        """
        return {}

    async def health_check(self) -> bool:
        """
        Check if Modal is accessible.

        TODO: Verify credentials
        """
        # Example:
        # import modal
        # try:
        #     modal.config.set_credentials(
        #         self.config["token_id"],
        #         self.config["token_secret"]
        #     )
        #     # Try to list apps
        #     modal.App.list()
        #     return True
        # except:
        #     return False

        return True

    def get_estimated_cost(self, gpu_type: str, duration_hours: float) -> Optional[float]:
        """
        Estimate Modal costs.

        Modal pricing (as of 2024):
        - CPU: $0.0001/CPU-sec ($0.36/CPU-hour)
        - GPU A100 40GB: $0.0023/sec ($8.28/hour)
        - GPU A100 80GB: $0.0030/sec ($10.80/hour)
        - GPU T4: $0.00051/sec ($1.84/hour)
        - GPU A10G: $0.00090/sec ($3.24/hour)
        """
        pricing = {
            "a100": 8.28,
            "a100-80gb": 10.80,
            "t4": 1.84,
            "a10g": 3.24,
            "any": 3.24,  # Default to A10G pricing
        }

        rate = pricing.get(gpu_type.lower(), 3.24)
        return rate * duration_hours
