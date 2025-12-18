from typing import Optional

import torch
from torch import nn, optim
from torch.utils.data import DataLoader


class AutoencoderTrainer:
    """Trainer class for autoencoder models."""

    def __init__(
        self,
        model: nn.Module,
        *,
        device,
        epochs: int,
        learning_rate: float,
        log_interval: int,
    ):
        self.device = device
        self.model = model.to(device)

        self.epochs = epochs
        self.learning_rate = learning_rate
        self.log_interval = log_interval

        self.loss_fn = nn.MSELoss()
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)

        self.train_losses: list[float] = []
        self.test_losses: list[float] = []

    def train_epoch(self, dataloader: DataLoader) -> float:
        """Train for one epoch."""
        # Enable dropout and batch normalization.
        self.model.train()
        train_loss = 0.0
        size = len(dataloader.dataset)  # type: ignore

        for batch_idx, batch in enumerate(dataloader):
            batch = batch.to(self.device)

            # Forward pass
            self.optimizer.zero_grad()
            predictions = self.model(batch)
            loss = self.loss_fn(predictions, batch)

            # Backward pass
            loss.backward()
            self.optimizer.step()

            train_loss += loss.item()

            # Logging
            if batch_idx % self.log_interval == 0:
                current = (batch_idx + 1) * len(batch)
                print(f"loss: {loss.item():>7f} [{current:>5d}/{size:>5d}]")

        avg_loss = train_loss / len(dataloader)
        return avg_loss

    def test_epoch(self, dataloader: DataLoader) -> float:
        """Evaluate on test set."""
        self.model.eval()
        test_loss = 0.0

        with torch.no_grad():
            for batch in dataloader:
                batch = batch.to(self.device)
                pred = self.model(batch)
                test_loss += self.loss_fn(pred, batch).item()
        avg_loss = test_loss / len(dataloader)
        print(f"Test Error: \n Avg loss: {avg_loss:>8f} \n")
        return avg_loss

    def fit(
        self, train_dataloader: DataLoader, test_dataloader: Optional[DataLoader] = None, epochs: Optional[int] = None
    ):
        epochs = epochs or self.epochs
        for epoch in range(1, epochs + 1):
            print(f"Epoch {epoch}\n-------------------------------")

            train_loss = self.train_epoch(train_dataloader)
            self.train_losses.append(train_loss)

            if test_dataloader is not None:
                test_loss = self.test_epoch(test_dataloader)
                self.test_losses.append(test_loss)

        print("Training complete!")

    def save_model(self, path: str):
        """Save model checkpoint"""
        torch.save(
            {
                "model_state_dict": self.model.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "train_losses": self.train_losses,
                "test_losses": self.test_losses,
            },
            path,
        )
        print(f"Model saved to {path}")

    def load_model(self, path: str):
        """Load model checkpoint"""
        checkpoint = torch.load(path, map_location=self.device)
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.train_losses = checkpoint.get("train_losses", [])
        self.test_losses = checkpoint.get("test_losses", [])
        print(f"Model loaded from {path}")
