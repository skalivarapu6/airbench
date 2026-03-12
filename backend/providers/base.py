"""
Base compute provider interface.
All compute providers must implement this abstract class.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from enum import Enum


class JobStatus(Enum):
    """Standardized job statuses across all providers"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProviderConfig(ABC):
    """Base class for provider-specific configuration"""
    pass


class BaseComputeProvider(ABC):
    """
    Abstract base class for compute providers.

    This provides a unified interface for submitting, monitoring,
    and managing ML training jobs across different cloud platforms.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the provider with configuration.

        Args:
            config: Provider-specific configuration dictionary
        """
        self.config = config or {}
        self._validate_config()

    @abstractmethod
    def _validate_config(self) -> None:
        """Validate that required configuration is present"""
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return the name of this provider (e.g., 'runpod', 'modal', 'local')"""
        pass

    @abstractmethod
    async def submit_job(
        self,
        experiment_id: int,
        base_model: str,
        dataset_path: str,
        hyperparameters: Dict[str, str],
        script_path: Optional[str] = None
    ) -> str:
        """
        Submit a training job to the compute provider.

        Args:
            experiment_id: Unique identifier for the experiment
            base_model: Name/path of the base model to fine-tune
            dataset_path: Path to the training dataset
            hyperparameters: Dictionary of hyperparameters
            script_path: Optional path to custom training script

        Returns:
            job_id: Provider-specific job identifier
        """
        pass

    @abstractmethod
    async def get_job_status(self, job_id: str) -> JobStatus:
        """
        Get the current status of a job.

        Args:
            job_id: Provider-specific job identifier

        Returns:
            JobStatus enum value
        """
        pass

    @abstractmethod
    async def get_job_logs(self, job_id: str, tail: int = 100) -> str:
        """
        Retrieve logs from a running or completed job.

        Args:
            job_id: Provider-specific job identifier
            tail: Number of lines to retrieve from end of logs

        Returns:
            Log output as string
        """
        pass

    @abstractmethod
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job.

        Args:
            job_id: Provider-specific job identifier

        Returns:
            True if cancellation successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_job_metrics(self, job_id: str) -> Dict[str, Any]:
        """
        Retrieve training metrics from a job.

        Args:
            job_id: Provider-specific job identifier

        Returns:
            Dictionary containing metrics (loss, accuracy, etc.)
        """
        pass

    async def health_check(self) -> bool:
        """
        Check if the provider is accessible and credentials are valid.

        Returns:
            True if provider is healthy, False otherwise
        """
        return True

    def get_estimated_cost(
        self,
        gpu_type: str,
        duration_hours: float
    ) -> Optional[float]:
        """
        Estimate the cost of running a job.

        Args:
            gpu_type: Type of GPU to use
            duration_hours: Expected duration in hours

        Returns:
            Estimated cost in USD, or None if not supported
        """
        return None
