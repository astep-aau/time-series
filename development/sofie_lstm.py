import time
from random import randint

import datasets as ds
import matplotlib.pyplot as plt
import numpy as np
import torch
from torch import Tensor, nn, optim
from torch.utils.data import DataLoader, Dataset

BATCH_SIZE = 32
SAMPLE_SIZE = 16
OVERLAP = 2
EMBEDDING_DIM = 4
SEED = randint(0, 100_000)
EPOCHS = 100
TEST_PERCENT = 0.2
THRESHOLD = 3.5

device = torch.accelerator.current_accelerator().type if torch.accelerator.is_available() else "cpu"  # type: ignore
generator = torch.Generator().manual_seed(SEED)


def timestamp_to_unix(batch):
    batch["timestamp"] = np.array(batch["timestamp"], dtype="datetime64[s]").astype("int64")
    return batch


url, OFFSET = (
    "https://github.com/numenta/NAB/raw/refs/heads/master/data/realAWSCloudwatch/ec2_cpu_utilization_24ae8d.csv",
    148,
)
# url, OFFSET = "https://github.com/numenta/NAB/raw/refs/heads/master/data/artificialWithAnomaly/art_daily_flatmiddle.csv", 0
# url, OFFSET = "https://github.com/numenta/NAB/raw/refs/heads/master/data/artificialNoAnomaly/art_daily_perfect_square_wave.csv", 0
# url, OFFSET = "https://github.com/numenta/NAB/raw/refs/heads/master/data/artificialWithAnomaly/art_load_balancer_spikes.csv", 95

dataset: ds.Dataset = (
    ds.load_dataset("csv", data_files=url, split="train")
    .map(timestamp_to_unix, batched=True)
    .train_test_split(test_size=TEST_PERCENT, shuffle=False, seed=SEED)  # type: ignore
    .with_format("torch", device=device)
)  # type: ignore


class SlidingWindowDataset(Dataset):
    def __init__(self, data: Tensor, window_size: int, overlap: int):
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


# Reshape 1 feature tensor [N] to [N, 1] to fit into RNN models.
# NOTE: Inefficient copy
train_data = torch.tensor(dataset["train"]["value"], device=device).to(device)  # type: ignore
# Z-score normalization
train_data -= train_data.mean((0), keepdim=True)
train_data /= train_data.std((0), keepdim=True)
train_data = train_data.unsqueeze(-1)
test_data = torch.tensor(dataset["test"]["value"], device=device).to(device)  # type: ignore
# Z-score normalization
# TODO: Merge Z-score normalization.
test_data -= test_data.mean((0), keepdim=True)
test_data /= test_data.std((0), keepdim=True)
test_data = test_data.unsqueeze(-1)

train_windowed = SlidingWindowDataset(train_data, window_size=SAMPLE_SIZE, overlap=OVERLAP)
test_windowed = SlidingWindowDataset(test_data, window_size=SAMPLE_SIZE, overlap=OVERLAP)

train_dl = DataLoader(train_windowed, batch_size=BATCH_SIZE, shuffle=True, generator=generator)
test_dl = DataLoader(test_windowed, batch_size=BATCH_SIZE, shuffle=True, generator=generator)


class LSTMAutoencoder(nn.Module):
    def __init__(self, seq_len, n_features, embedding_dim=64):
        super(LSTMAutoencoder, self).__init__()

        self.seq_len = seq_len
        self.n_features = n_features
        self.internal_dim, self.hidden_dim = embedding_dim, 4 * embedding_dim

        # Encoder
        self.encoder_lstm1 = nn.LSTM(input_size=n_features, hidden_size=self.hidden_dim, num_layers=1, batch_first=True)
        self.encoder_lstm2 = nn.LSTM(
            input_size=self.hidden_dim, hidden_size=self.internal_dim, num_layers=1, batch_first=True
        )

        # Decoder
        self.decoder_lstm1 = nn.LSTM(
            input_size=self.internal_dim, hidden_size=self.internal_dim, num_layers=1, batch_first=True
        )
        self.decoder_lstm2 = nn.LSTM(
            input_size=self.internal_dim, hidden_size=self.hidden_dim, num_layers=1, batch_first=True
        )

        # Output layer
        # TODO: https://discuss.pytorch.org/t/any-pytorch-function-can-work-as-keras-timedistributed/1346/28
        self.output_layer = nn.Linear(self.hidden_dim, n_features)

        # Activation
        self.relu = nn.ReLU()

    def forward(self, x):
        # x - shape (batch_size, seq_len, n_features)

        # Encoder
        enc_out1, _ = self.encoder_lstm1(x)
        enc_out1 = self.relu(enc_out1)

        enc_out2, _ = self.encoder_lstm2(enc_out1)
        enc_out2 = self.relu(enc_out2)

        # Latent space
        # encoded = enc_out2[:, -1:, :]  # shape: (batch_size, 1, hidden_dim2)
        # repeated = encoded.repeat(1, self.seq_len, 1) # shape: (batch_size, seq_len, hidden_dim2)
        repeated = enc_out2

        # Decoder
        dec_out1, _ = self.decoder_lstm1(repeated)
        dec_out1 = self.relu(dec_out1)

        dec_out2, _ = self.decoder_lstm2(dec_out1)
        dec_out2 = self.relu(dec_out2)

        output = self.output_layer(dec_out2)

        return output


def train(dataloader, model, loss_fn, optimizer):
    size = len(dataloader.dataset)  # type: ignore

    # Possibly enable dropout and batch normalization.
    model.train()

    for batch_idx, batch in enumerate(dataloader):
        optimizer.zero_grad()

        predictions = model(batch)
        loss = loss_fn(predictions, batch)

        # Backpropagation
        loss.backward()
        optimizer.step()

        if batch_idx % 10 == 0:
            loss, current = loss.item(), (batch_idx + 1) * len(batch)
            print(f"loss: {loss:>7f} [{current:>5d}/{size:>5d}]")


# Testing
def test(dataloader, model, loss_fn):
    n_batches = len(dataloader)
    model.eval()
    test_loss = 0.0
    with torch.no_grad():
        for batch in dataloader:
            pred = model(batch)
            test_loss += loss_fn(pred, batch).item()
    test_loss /= n_batches
    print(f"Test Error: \n Avg loss: {test_loss:>8f} \n")


time.sleep(1)

model = LSTMAutoencoder(seq_len=SAMPLE_SIZE, n_features=1, embedding_dim=EMBEDDING_DIM).to(device)

# Loss and optimizer
loss_fn = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=1e-3)


for epoch in range(1, EPOCHS + 1):
    print(f"Epoch {epoch}\n-------------------------------")
    train(train_dl, model, loss_fn, optimizer)
    test(test_dl, model, loss_fn)

print("Done!")
# Print model summary
print(model)
print(f"\nTotal parameters: {sum(p.numel() for p in model.parameters())}")

sample = train_data[OFFSET : OFFSET + SAMPLE_SIZE * 8].reshape(-1, SAMPLE_SIZE, 1)

print(f"Input: {sample.shape}: {sample}")

with torch.no_grad():
    predictions = model(sample)

print(f"Output: {predictions.shape}: {predictions}")

plt.plot(sample.reshape(-1).numpy(force=True))
plt.plot(predictions.reshape(-1).numpy(force=True))
plt.show()

reconstruction_error = torch.abs(sample - predictions)
anomalies = reconstruction_error > THRESHOLD
plt.plot(reconstruction_error.reshape(-1).numpy(force=True))
plt.plot(anomalies.reshape(-1).numpy(force=True))
plt.show()
