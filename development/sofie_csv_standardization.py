import datasets as ds
import numpy as np


def timestamp_to_unix(batch):
    batch["timestamp"] = np.array(batch["timestamp"], dtype="datetime64[s]").astype("int64")
    return batch


URL, NAME = (
    "https://github.com/numenta/NAB/raw/refs/heads/master/data/realAWSCloudwatch/ec2_cpu_utilization_24ae8d.csv",
    "ec2.csv",
)
URL, NAME = (
    "https://github.com/numenta/NAB/raw/refs/heads/master/data/realAWSCloudwatch/ec2_cpu_utilization_fe7f93.csv",
    "ec2_2.csv",
)
# URL, NAME = "https://github.com/numenta/NAB/raw/refs/heads/master/data/artificialWithAnomaly/art_daily_flatmiddle.csv", "art_daily_faltmiddle.csv"
# URL, NAME = "https://github.com/numenta/NAB/raw/refs/heads/master/data/artificialNoAnomaly/art_daily_perfect_square_wave.csv", "art_daily_perfect_square_wave.csv"
# URL, NAME = "https://github.com/numenta/NAB/raw/refs/heads/master/data/artificialWithAnomaly/art_load_balancer_spikes.csv", "art_load_balancer_spikes.csv"

dataset: ds.Dataset = ds.load_dataset("csv", data_files=URL, split="train").map(timestamp_to_unix, batched=True)  # type: ignore

dataset = dataset.rename_columns({"timestamp": "unix_time", "value": "values"})

dataset.to_csv(NAME)
