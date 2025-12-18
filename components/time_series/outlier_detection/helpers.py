import math
from random import randrange
from typing import Literal, Optional, Tuple

import torch
from pydantic import BaseModel, Field, field_validator
from torch.utils.data import Dataset, Subset


class DatasetConfig(BaseModel):
    """Configuration for dataset loading and processing"""

    sequence_length: int = Field(default=32, gt=0, description="Sequence length")
    stride: int = Field(default=1, gt=0)
    test_size: float = Field(default=0.2, gt=0, lt=1.0)
    shuffle: bool = Field(default=False)
    normalize: Optional[Literal["robust", "robust_extreme", "zscore"]] = Field(default=None)


class HyperparameterConfig(BaseModel):
    """Configuration for training parameters"""

    batch_size: int = Field(default=32, gt=0)
    hidden_size: int = Field(default=32, gt=0)
    internal_size: int = Field(default=16, gt=0)
    # latent_size: int = Field(default=1, gt=0)
    learning_rate: float = Field(default=1e-3, gt=0.0, le=1.0)
    # num_layers: int = Field(default=2, gt=0)


class TrainingConfig(BaseModel):
    """Configuration for training settings"""

    epochs: int = Field(default=100, gt=0)
    log_interval: int = Field(default=10, gt=0)


class AnalysisConfig(BaseModel):
    """Complete analysys configuration."""

    seed: Optional[int] = Field(default=None, gt=0)
    threshold: float = Field(default=3.5, gt=0)
    device: Optional[Literal["cpu", "cuda", "mtia", "xpu", "mps", "hpu"]] = Field(default=None)

    dataset: DatasetConfig = Field(default_factory=DatasetConfig)
    hyperparameters: HyperparameterConfig = Field(default_factory=HyperparameterConfig)
    training: TrainingConfig = Field(default_factory=TrainingConfig)

    @field_validator("seed", mode="before")
    @classmethod
    def set_seed(cls, v):
        if v is None:
            return randrange(0, 1_000_000)
        return v

    @field_validator("device", mode="before")
    @classmethod
    def set_device(cls, v):
        if v is None:
            return (
                torch.accelerator.current_accelerator().type  # type: ignore
                if torch.accelerator.is_available()
                else "cpu"
            )
        return v


def create_train_test_split(
    dataset: Dataset, test_size: float = 0.2, shuffle: bool = False, generator: Optional[torch.Generator] = None
) -> Tuple[Subset, Subset]:
    """Create train/test splits for a dataset"""
    if not 0 < test_size < 1:
        raise ValueError("test_size must be between 0 and 1")

    total_size = len(dataset)  # type: ignore
    test_count = math.floor(total_size * test_size)
    train_count = total_size - test_count

    if shuffle:
        indices = torch.randperm(total_size, generator=generator).tolist()
    else:
        indices = list(range(total_size))

    train_indices = indices[:train_count]
    test_indices = indices[train_count:]

    train_dataset = Subset(dataset, train_indices)
    test_dataset = Subset(dataset, test_indices)

    return train_dataset, test_dataset
