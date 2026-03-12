"""
Lambda Labs compute provider integration.

Lambda Labs offers dedicated GPU cloud instances with competitive pricing.
Docs: https://docs.lambdalabs.com/
"""
import logging
from typing import Dict, Any, Optional
from .base import BaseComputeProvider, JobStatus

logger = logging.getLogger(__name__)


class LambdaLabsProvider(BaseComputeProvider):
    """
    Lambda Labs provider for GPU instances.

    Configuration required:
    - api_key: Lambda Labs API key
    - instance_type: (optional) Instance type (e.g., 'gpu_1x_a100')
    - ssh_key_name: SSH key name for instance access
    """

    def _validate_config(self) -> None:
        """Validate Lambda Labs configuration"""
        if "api_key" not in self.config:
            raise ValueError("Lambda Labs API key is required. Set 'api_key' in config.")

    @property
    def provider_name(self) -> str:
        return "lambda"

    async def submit_job(
        self,
        experiment_id: int,
        base_model: str,
        dataset_path: str,
        hyperparameters: Dict[str, str],
        script_path: Optional[str] = None
    ) -> str:
        """
        Submit a job to Lambda Labs.

        TODO: Implement Lambda Labs API integration.
        Steps:
        1. Launch an instance with specified GPU type
        2. SSH into instance and setup environment
        3. Copy training script and dataset
        4. Start training job in background
        5. Return instance ID as job_id
        """
        # TEMPLATE IMPLEMENTATION

        api_key = self.config["api_key"]
        instance_type = self.config.get("instance_type", "gpu_1x_a100")
        ssh_key_name = self.config.get("ssh_key_name")

        # Example pseudo-code for Lambda Labs API:
        # import requests
        #
        # headers = {"Authorization": f"Bearer {api_key}"}
        # payload = {
        #     "region_name": "us-west-1",
        #     "instance_type_name": instance_type,
        #     "ssh_key_names": [ssh_key_name],
        #     "name": f"experiment-{experiment_id}"
        # }
        #
        # response = requests.post(
        #     "https://cloud.lambdalabs.com/api/v1/instance-operations/launch",
        #     headers=headers,
        #     json=payload
        # )
        #
        # instance_id = response.json()["data"]["instance_ids"][0]
        #
        # # Wait for instance to be ready, then SSH and start training
        # # ...
        #
        # return instance_id

        job_id = f"lambda_{experiment_id}"
        logger.warning("Lambda Labs provider is a stub — returning mock job ID %s", job_id)
        return job_id

    async def get_job_status(self, job_id: str) -> JobStatus:
        """
        Get job status from Lambda Labs.

        TODO: Query instance status and check if training is running
        """
        # Example:
        # import requests
        # headers = {"Authorization": f"Bearer {self.config['api_key']}"}
        # response = requests.get(
        #     f"https://cloud.lambdalabs.com/api/v1/instances/{job_id}",
        #     headers=headers
        # )
        # status = response.json()["data"]["status"]
        # status_map = {
        #     "active": JobStatus.RUNNING,
        #     "booting": JobStatus.QUEUED,
        #     "terminated": JobStatus.COMPLETED,
        # }
        # return status_map.get(status, JobStatus.QUEUED)

        return JobStatus.QUEUED

    async def get_job_logs(self, job_id: str, tail: int = 100) -> str:
        """
        Retrieve logs from Lambda Labs instance.

        TODO: SSH into instance and read training logs
        """
        # Example:
        # import paramiko
        # ssh = paramiko.SSHClient()
        # ssh.connect(instance_ip, username="ubuntu", key_filename=key_path)
        # stdin, stdout, stderr = ssh.exec_command(f"tail -n {tail} /path/to/training.log")
        # logs = stdout.read().decode()
        # ssh.close()
        # return logs

        return f"[Lambda Labs] Logs for {job_id} (not implemented)"

    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a Lambda Labs job by terminating the instance.

        TODO: Terminate the instance via API
        """
        # Example:
        # import requests
        # headers = {"Authorization": f"Bearer {self.config['api_key']}"}
        # response = requests.post(
        #     "https://cloud.lambdalabs.com/api/v1/instance-operations/terminate",
        #     headers=headers,
        #     json={"instance_ids": [job_id]}
        # )
        # return response.status_code == 200

        return False

    async def get_job_metrics(self, job_id: str) -> Dict[str, Any]:
        """
        Retrieve metrics from Lambda Labs job.

        TODO: SSH and parse training logs or metrics files
        """
        return {}

    async def health_check(self) -> bool:
        """
        Check if Lambda Labs API is accessible.

        TODO: Verify API key by listing instances
        """
        # Example:
        # import requests
        # try:
        #     headers = {"Authorization": f"Bearer {self.config['api_key']}"}
        #     response = requests.get(
        #         "https://cloud.lambdalabs.com/api/v1/instances",
        #         headers=headers
        #     )
        #     return response.status_code == 200
        # except:
        #     return False

        return True

    def get_estimated_cost(self, gpu_type: str, duration_hours: float) -> Optional[float]:
        """
        Estimate Lambda Labs costs.

        Lambda Labs pricing (as of 2024):
        - 1x A100 (40GB): $1.10/hr
        - 1x A100 (80GB): $1.29/hr
        - 8x A100 (80GB): $10.32/hr
        - 1x H100: $2.49/hr
        """
        pricing = {
            "gpu_1x_a100": 1.10,
            "gpu_1x_a100_sxm4": 1.29,
            "gpu_8x_a100_80gb_sxm4": 10.32,
            "gpu_1x_h100_pcie": 2.49,
        }

        rate = pricing.get(gpu_type, 1.10)
        return rate * duration_hours
