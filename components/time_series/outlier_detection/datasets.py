from typing import Any, Optional

import numpy as np
import torch
from sqlmodel import Session, select
from time_series.database import DatapointRepository, Dataset


class DatapointSQLDataset(torch.utils.data.Dataset):
    def __init__(
        self, session: Session, dataset_id: int, sequence_length: int, stride: int, scaler: Optional[Any] = None
    ):
        self.session = session
        self.dataset_id = dataset_id
        self.sequence_length = sequence_length
        self.stride = stride
        self.scaler = scaler

        self._load_data()

    def _load_data(self):
        # Load everything to speed up learning over chunking this into a bunch of queries.
        # Database may not be locally available.
        datapoints = DatapointRepository(session=self.session).get_by_dataset(self.dataset_id)

        # Handle empty response explicitly as an error, as we cannot continue without some data.
        if not datapoints:
            dataset_exists = self.session.exec(select(True).where(Dataset.id == self.dataset_id).limit(1)).first()
            if not dataset_exists:
                raise ValueError(f"Dataset with id={self.dataset_id} does not exist")
            raise ValueError(f"No datapoints found for dataset_id={self.dataset_id}")

        # List to map actual timestamps to each time step for all values.
        self.timestamps = [datapoint.time for datapoint in datapoints]

        # Normalization
        values = np.array([datapoint.value for datapoint in datapoints], dtype=np.float32)
        if self.scaler is not None:
            # Log1p to handle zero and near zero values.
            # values = np.log1p(data.reshape(-1, 1))
            self.values = torch.tensor(self.scaler.fit_transform(values.reshape(-1, 1)).flatten(), dtype=torch.float32)
        else:
            # Assume data is already normalized by the caller.
            self.values = torch.tensor(values, dtype=torch.float32)

        self.num_sequences = max(0, (len(self.values) - self.sequence_length) // self.stride + 1)

    def __len__(self) -> int:
        return self.num_sequences

    def __getitem__(self, idx: int) -> torch.Tensor:
        if idx < 0 or idx >= self.num_sequences:
            raise IndexError(f"Index {idx} out of range [0, {self.num_sequences})")

        start_idx = idx * self.stride
        sequence = self.values[start_idx : start_idx + self.sequence_length]

        # Reshape into [sequence_length, 1]
        return sequence.reshape(-1, 1)

    def get_timestamps(self, idx: int) -> list:
        if idx < 0 or idx >= self.num_sequences:
            raise IndexError(f"Index {idx} out of range [0, {self.num_sequences})")

        start_idx = idx * self.stride
        timestamps = self.timestamps[start_idx : start_idx + self.sequence_length]

        return timestamps


class SlidingWindowDataset(torch.utils.data.Dataset):
    def __init__(self, data: torch.Tensor, window_size: int, overlap: int):
        self.window_size = window_size
        self.overlap = overlap
        self.stride = window_size - overlap
        self.data = data
        self.data_length = len(self.data)
        self.num_windows = max(0, (self.data_length - window_size) // self.stride + 1)

    def __len__(self):
        return self.num_windows

    def __getitem__(self, idx):
        start_idx = idx * self.stride
        end_idx = start_idx + self.window_size
        return self.data[start_idx:end_idx]
