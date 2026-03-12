"""
Compute provider implementations.
"""
from .base import BaseComputeProvider, JobStatus, ProviderConfig
from .local import LocalProvider
from .runpod import RunPodProvider
from .lambda_labs import LambdaLabsProvider
from .modal_provider import ModalProvider

__all__ = [
    "BaseComputeProvider",
    "JobStatus",
    "ProviderConfig",
    "LocalProvider",
    "RunPodProvider",
    "LambdaLabsProvider",
    "ModalProvider",
]


def get_provider(provider_name: str, config: dict = None) -> BaseComputeProvider:
    """
    Factory function to get a provider instance.

    Args:
        provider_name: Name of the provider ('local', 'runpod', 'lambda', 'modal')
        config: Provider-specific configuration

    Returns:
        Instance of the requested provider

    Raises:
        ValueError: If provider name is not recognized
    """
    providers = {
        "local": LocalProvider,
        "runpod": RunPodProvider,
        "lambda": LambdaLabsProvider,
        "modal": ModalProvider,
    }

    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        raise ValueError(
            f"Unknown provider: {provider_name}. "
            f"Available providers: {', '.join(providers.keys())}"
        )

    return provider_class(config)
