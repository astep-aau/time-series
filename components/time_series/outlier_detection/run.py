import datetime
from itertools import compress

import torch
from sklearn.preprocessing import RobustScaler, StandardScaler
from sqlmodel import Session
from time_series.database import UnitOfWork, get_engine
from time_series.database.models import StatusType
from time_series.outlier_detection import (
    AnalysisConfig,
    AutoencoderTrainer,
    DatapointSQLDataset,
    LSTMAutoencoder,
    create_train_test_split,
)
from torch.utils.data import DataLoader, Dataset


def get_scaler(name: str | None):
    match name:
        case "robust":
            return RobustScaler()
        case "robust_extreme":
            return RobustScaler(quantile_range=(10, 90))
        case "zscore":
            return StandardScaler()
        case None:
            return None
        case _:
            raise ValueError(f"Unrecognized scaler: {name}")


def run_lstmae_analysis(dataset_id: int, analysis_id: int, config: AnalysisConfig):
    with Session(get_engine()) as session, UnitOfWork(session=session) as uow:
        uow.analyses.update(analysis_id, status=StatusType.processing)
        uow.commit()

        datapoint_dataset = DatapointSQLDataset(
            session=session,
            dataset_id=dataset_id,
            sequence_length=config.dataset.sequence_length,
            stride=config.dataset.stride,
            scaler=get_scaler(config.dataset.normalize),
        )

        trainer = train_lstmae(datapoint_dataset, config=config)
        _prediction, error = run_lstmae_prediction(datapoint_dataset, model=trainer.model, config=config)
        outlier_mask = create_outlier_mask(error, threshold=config.threshold)
        anomalies = group_anomalies(analysis_id, timestamps=datapoint_dataset.timestamps, outlier_mask=outlier_mask)

        uow.anomalies.bulk_create(anomalies)
        uow.commit()

        uow.analyses.update(analysis_id, status=StatusType.completed)
        uow.commit()


def train_lstmae(dataset: Dataset, config: AnalysisConfig):
    generator = torch.Generator(config.device).manual_seed(config.seed) if config.seed else None

    train_dataset, test_dataset = create_train_test_split(
        dataset=dataset,
        test_size=config.dataset.test_size,
        shuffle=config.dataset.shuffle,
        generator=generator,
    )

    model = LSTMAutoencoder(
        sequence_length=config.dataset.sequence_length,
        n_features=1,
        internal_size=config.hyperparameters.internal_size,
        hidden_size=config.hyperparameters.hidden_size,
    )

    trainer = AutoencoderTrainer(
        model=model,
        device=config.device,
        epochs=config.training.epochs,
        learning_rate=config.hyperparameters.learning_rate,
        log_interval=config.training.log_interval,
    )

    train_dataloader = DataLoader(
        dataset=train_dataset,
        batch_size=config.hyperparameters.batch_size,
        shuffle=config.dataset.shuffle,
        generator=generator,
    )

    test_dataloader = DataLoader(
        dataset=test_dataset,
        batch_size=config.hyperparameters.batch_size,
        shuffle=config.dataset.shuffle,
        generator=generator,
    )

    trainer.fit(train_dataloader=train_dataloader, test_dataloader=test_dataloader)

    return trainer


def run_lstmae_prediction(dp_ds: DatapointSQLDataset, model: torch.nn.Module, config: AnalysisConfig):
    predictions_list = []

    model.eval()
    with torch.no_grad():
        for idx in range(len(dp_ds)):
            actual = dp_ds[idx].unsqueeze(0)  # shape: [1, n, 1]

            prediction = model(actual)
            predictions_list.append(prediction)

    predictions = torch.cat(predictions_list)

    n_timesteps = len(dp_ds.timestamps)
    pred_counts = torch.zeros(n_timesteps)
    pred_sums = torch.zeros(n_timesteps)
    error_sums = torch.zeros(n_timesteps)

    for idx in range(len(dp_ds)):
        start_idx = idx
        end_idx = start_idx + config.dataset.sequence_length

        actual_seq = dp_ds[idx].squeeze()  # shape: [sequence_length]
        pred_seq = predictions[idx].squeeze()  # shape: [sequence_length]

        error_seq = torch.abs(actual_seq - pred_seq)

        pred_sums[start_idx:end_idx] += pred_seq
        error_sums[start_idx:end_idx] += error_seq
        pred_counts[start_idx:end_idx] += 1

    averaged_prediction = pred_sums / pred_counts
    averaged_error = error_sums / pred_counts

    return averaged_prediction, averaged_error


def create_outlier_mask(error, threshold: float = 3.5):
    log_error = torch.log(error + 1e-6)

    median = torch.median(log_error)
    mad = torch.median(torch.abs(log_error - median))
    # z-score against 75th percentile
    modified_z_scores = 0.6745 * (log_error - median) / (mad + 1e-8)

    outlier_mask = torch.abs(modified_z_scores) > threshold

    return outlier_mask


def group_anomalies(analysis_id: int, timestamps: list[datetime.datetime], outlier_mask):
    distance = timestamps[1] - timestamps[0]
    outlier_timestamps = list(compress(timestamps, outlier_mask))
    group_outlier_timestamps = group_timestamps(outlier_timestamps, distance=distance)

    def to_anomaly_dict(start: datetime.datetime, end: datetime.datetime):
        return {"analysis_id": analysis_id, "start": start, "end": end, "type": "point"}

    anomalies = list(map(lambda args: to_anomaly_dict(*args), group_outlier_timestamps))
    return anomalies


def group_timestamps(
    timestamps: list[datetime.datetime], distance: datetime.timedelta
) -> list[tuple[datetime.datetime, datetime.datetime]]:
    if not timestamps:
        return []

    groups = []
    start = timestamps[0]
    end = timestamps[0]

    for i in range(1, len(timestamps)):
        if timestamps[i] - timestamps[i - 1] == distance:
            end = timestamps[i]
        else:
            groups.append((start, end))
            start = timestamps[i]
            end = timestamps[i]

    groups.append((start, end))

    return groups
