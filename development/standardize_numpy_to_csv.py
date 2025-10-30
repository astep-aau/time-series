import os
from datetime import datetime
from typing import Union

import numpy as np
import pandas as pd

# NOTE: This utility requires pandas and numpy to be installed in your environment.


def standardize_numpy_to_csv(
    numpy_file_path: str = "name.npy",
    output_filename: str = "standardized_output.csv",
    sample_rate_seconds: int = 60,
    column_index: int = 0,
) -> Union[str, None]:
    try:
        if not os.path.exists(numpy_file_path):
            print(f"ERROR: NumPy file not found at path: {numpy_file_path}. Please check file location.")
            return None

        data_matrix = np.load(numpy_file_path)

        values = data_matrix[:, column_index].astype(np.float64)

        num_samples = len(values)

        start_epoch = int(datetime(2025, 1, 1).timestamp())

        time_index = np.arange(num_samples) * sample_rate_seconds
        unix_time = (start_epoch + time_index).astype(np.int64)

        df = pd.DataFrame({"unix_time": unix_time, "values": values})

        output_dir = os.path.dirname(output_filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        df.to_csv(output_filename, index=False)

        return output_filename

    except IndexError:
        cols = data_matrix.shape[1] if "data_matrix" in locals() else "N/A"
        print(f"ERROR: Column index {column_index} is out of bounds. Dataset has {cols} columns.")
        return None
    except Exception as e:
        print(f"An unexpected ERROR occurred during CSV export: {e}")
        return None


# NOTE: This block runs when the file is executed directly (e.g., via python script.py).
if __name__ == "__main__":
    input_npy = "file_name.npy"

    output_csv = "output_file_name.csv"

    print(f"Attempting to standardize data from '{input_npy}'...")

    result_path = standardize_numpy_to_csv(
        numpy_file_path=input_npy, output_filename=output_csv, sample_rate_seconds=60, column_index=0
    )

    if result_path:
        print(f"SUCCESS: The file was created at: {result_path}")
    else:
        print("FAILURE: The CSV file was not created. Check the errors above.")
