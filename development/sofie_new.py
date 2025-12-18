import numpy as np
from sqlmodel import Session
from time_series.database import UnitOfWork, get_engine
from time_series.outlier_detection import (
    AnalysisConfig,
    DatapointSQLDataset,
    DatasetConfig,
    HyperparameterConfig,
    TrainingConfig,
)
from time_series.outlier_detection.run import (
    create_outlier_mask,
    get_scaler,
    group_anomalies,
    run_lstmae_analysis,
    run_lstmae_prediction,
    train_lstmae,
)

NAME = "Test Analysis"
DESCRIPTION = "Yes"

# S-1
DATASET_ID = 10
TEST_PERCENT = 0.7223371760764608

# E-1
# DATASET_ID = 11
# TEST_PERCENT = 0.7472797472797473

# P-1
# DATASET_ID = 12
# TEST_PERCENT = 0.7475608684187396

session = Session(get_engine())
config = AnalysisConfig(
    training=TrainingConfig(epochs=30),
    dataset=DatasetConfig(
        sequence_length=16, stride=1, shuffle=False, test_size=TEST_PERCENT, normalize="robust_extreme"
    ),
    hyperparameters=HyperparameterConfig(hidden_size=64, internal_size=32),
)

if False:
    with UnitOfWork(session=session) as uow:
        analysis = uow.analyses.create(
            dataset_id=DATASET_ID,
            detection_method="lstmae",
            name=NAME,
            description=DESCRIPTION,
        )
        uow.commit()
    run_lstmae_analysis(dataset_id=DATASET_ID, analysis_id=analysis.id, config=config)
    exit()


dp_ds = DatapointSQLDataset(
    session=session,
    dataset_id=DATASET_ID,
    sequence_length=config.dataset.sequence_length,
    stride=config.dataset.stride,
    scaler=get_scaler(config.dataset.normalize),
)

trainer = train_lstmae(dp_ds, config=config)
prediction, error = run_lstmae_prediction(dp_ds, model=trainer.model, config=config)
outlier_mask = create_outlier_mask(error)
anomalies = group_anomalies(analysis_id=0, timestamps=dp_ds.timestamps, outlier_mask=outlier_mask)

print(len(anomalies))


def plot_error_outlier_mask(dataset: DatapointSQLDataset, error, outlier_mask):
    import matplotlib.pyplot as plt

    plt.figure(figsize=(14, 6))
    plt.plot(dataset.values, label="Data", color="blue")
    plt.plot(error.numpy(), label="Reconstruction Error", color="red")
    plt.xlabel("Time Step")
    plt.ylabel("Value")

    y_min, y_max = plt.ylim()
    x = np.arange(len(outlier_mask))

    plt.fill_between(
        x, y_min, y_max, where=(outlier_mask.numpy()), alpha=0.3, zorder=0, color="orange", label="Outliers"
    )

    plt.legend()
    plt.show()


def plot_actual_predicted(actual, predicted):
    import matplotlib.pyplot as plt

    plt.plot(actual, label="Actual", color="blue")
    plt.plot(predicted, label="Predicted", color="red")
    plt.xlabel("Time Step")
    plt.ylabel("Value")

    plt.legend()
    plt.show()


plot_error_outlier_mask(dp_ds, error, outlier_mask)
plot_actual_predicted(actual=dp_ds.values, predicted=prediction)
