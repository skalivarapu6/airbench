from __future__ import annotations

from typing import Optional, List
from sqlalchemy import (
    String, Integer, DateTime, Float, Boolean,
    ForeignKey, Text, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column, relationship
)
from datetime import datetime

from sqlalchemy import Enum
import enum

class PhaseEnum(enum.Enum):
    train = "train"
    eval = "eval"
    final = "final"

class Base(DeclarativeBase):
    pass

# ------------------------------------------------------------------
# Models
# ------------------------------------------------------------------

class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    file_path: Mapped[Optional[str]] = mapped_column(Text)
    num_samples: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    checksum: Mapped[Optional[str]] = mapped_column(String(64))
    experiments: Mapped[List["Experiment"]] = relationship(back_populates="dataset")

    def __repr__(self) -> str:
        return f"<Dataset id={self.id} name={self.name}>"

class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    base_model: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="queued")

    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE")
    )
    dataset: Mapped["Dataset"] = relationship(back_populates="experiments")

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    compute_provider: Mapped[Optional[str]] = mapped_column(String(50))
    remote_job_id: Mapped[Optional[str]] = mapped_column(String(100))
    compute_config: Mapped[Optional[dict]] = mapped_column(JSONB)

    final_train_loss: Mapped[Optional[float]] = mapped_column(Float)
    final_val_loss: Mapped[Optional[float]] = mapped_column(Float)
    test_accuracy: Mapped[Optional[float]] = mapped_column(Float)

    log_file_path: Mapped[Optional[str]] = mapped_column(Text)
    checkpoint_path: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    hyperparameters: Mapped[List["Hyperparameter"]] = relationship(
        back_populates="experiment",
        cascade="all, delete-orphan",
    )

    metrics: Mapped[List["Metric"]] = relationship(
        back_populates="experiment",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Experiment id={self.id} name={self.name} status={self.status}>"

class Hyperparameter(Base):
    __tablename__ = "hyperparameters"

    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE")
    )

    param_name: Mapped[str] = mapped_column(String(100))
    param_value: Mapped[str] = mapped_column(Text, nullable=False)
    param_type: Mapped[Optional[str]] = mapped_column(String(20))
    param_category: Mapped[Optional[str]] = mapped_column(String(50))
    is_default: Mapped[bool] = mapped_column(Boolean, default=True)

    experiment: Mapped["Experiment"] = relationship(back_populates="hyperparameters")

    def __repr__(self) -> str:
        return f"<Hyperparameter {self.param_name}={self.param_value}>"

class Metric(Base):
    """
    Tracks metrics during training and evaluation.

    step values:
    - NULL: Inference-only (no training, just evaluation)
    - 0: Pre-training baseline
    - >0: Training step or post-training eval

    phase values:
    - train: Logged during training
    - eval: Evaluation metrics
    - inference: Testing external/pre-trained models
    """
    __tablename__ = "metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    experiment_id: Mapped[int] = mapped_column(
        ForeignKey("experiments.id", ondelete="CASCADE")
    )

    step: Mapped[int | None]
    phase: Mapped[PhaseEnum] = mapped_column(
        Enum(PhaseEnum, name="phase_enum"),
        nullable=False,
        default=PhaseEnum.train
    )
    metric_name: Mapped[str] = mapped_column(String(100))
    metric_value: Mapped[float]
    timestamp: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    experiment: Mapped["Experiment"] = relationship(back_populates="metrics")

    def __repr__(self) -> str:
        return f"<Metric {self.metric_name} step={self.step} value={self.metric_value}>"
