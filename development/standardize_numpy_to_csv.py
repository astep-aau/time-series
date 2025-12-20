import os
from datetime import datetime
from typing import Union

import numpy as np
import pandas as pd


def standardize_numpy_to_csv(
    data_path: str = "csvs/nasa/data/data",
    numpy_filename: str = "name.npy",
    output_filename: str = "standardized_output.csv",
    sample_rate_seconds: int = 60,
    column_index: int = 0,
) -> Union[str, None]:
    try:
        train_path = f"{data_path}/train/{numpy_filename}"
        test_path = f"{data_path}/test/{numpy_filename}"

        if not os.path.exists(train_path):
            print(f"ERROR: NumPy file not found at path: {train_path!r}. Please check file location.")
            return None

        train_matrix = np.load(train_path)[:, column_index]
        test_matrix = np.load(test_path)[:, column_index]

        values = np.concatenate([train_matrix.astype(np.float64), test_matrix.astype(np.float64)])

        num_samples = len(values)
        print(f"Size of combined array: {num_samples}")
        print(f"Test-percentage: {test_matrix.shape[0] / num_samples}")

        start_epoch = int(datetime(2025, 1, 1).timestamp())

        time_index = np.arange(num_samples) * sample_rate_seconds
        unix_time = (start_epoch + time_index).astype(np.int64)

        df = pd.DataFrame({"unix_time": unix_time, "values": values})

        output_dir = os.path.dirname(output_filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        df.to_csv(output_filename, index=False)

        return output_filename

    except Exception as e:
        print(f"An unexpected ERROR occurred during CSV export: {e}")
        return None


if __name__ == "__main__":
    nasa_data_path = "csvs/nasa/data/data"
    numpy_file = "S-1.npy"

    output_csv = "S-1.csv"

    print(f"Attempting to standardize data from '{numpy_file}'...")

    result_path = standardize_numpy_to_csv(
        data_path=nasa_data_path,
        numpy_filename=numpy_file,
        output_filename=output_csv,
        sample_rate_seconds=60,
        column_index=0,
    )

    if result_path:
        print(f"SUCCESS: The file was created at: {result_path}")
    else:
        print("FAILURE: The CSV file was not created. Check the errors above.")
