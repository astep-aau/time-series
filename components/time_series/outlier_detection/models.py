from torch import nn


class LSTMAutoencoder(nn.Module):
    def __init__(self, sequence_length, n_features=1, internal_size=16, hidden_size=64):
        super(LSTMAutoencoder, self).__init__()

        self.seq_len = sequence_length
        self.n_features = n_features
        self.internal_dim, self.outer_dim = internal_size, hidden_size
        self.latent_size = 1
        self.dropout_percent = 0.1

        self.dropout = nn.Dropout(self.dropout_percent)

        # Encoder
        self.encoder_lstm1 = nn.LSTM(input_size=n_features, hidden_size=self.outer_dim, num_layers=1, batch_first=True)
        self.encoder_lstm2 = nn.LSTM(
            input_size=self.outer_dim, hidden_size=self.internal_dim, num_layers=1, batch_first=True
        )

        self.latent_space = nn.Linear(
            in_features=self.internal_dim,
            out_features=self.latent_size,
        )

        # Decoder
        self.decoder_lstm1 = nn.LSTM(
            input_size=self.latent_size, hidden_size=self.internal_dim, num_layers=1, batch_first=True
        )
        self.decoder_lstm2 = nn.LSTM(
            input_size=self.internal_dim, hidden_size=self.outer_dim, num_layers=1, batch_first=True
        )

        # Output layer
        # TODO: https://discuss.pytorch.org/t/any-pytorch-function-can-work-as-keras-timedistributed/1346/28
        self.output_layer = nn.Linear(self.outer_dim, n_features)

        # Activation
        self.relu = nn.ReLU()

    def forward(self, x):
        # x - shape (batch_size, seq_len, n_features)

        # Encoder
        enc_out1, _ = self.encoder_lstm1(x)
        # enc_out1 = self.relu(enc_out1)
        enc_out1 = self.dropout(enc_out1)

        enc_out2, _ = self.encoder_lstm2(enc_out1)
        # enc_out2 = self.relu(enc_out2)
        enc_out2 = self.dropout(enc_out2)

        # Latent space

        # latent_space = enc_out2[:, -1:, :]  # shape: (batch_size, 1, hidden_dim2)
        # latent_space = latent_space.repeat(1, self.seq_len, 1)  # shape: (batch_size, seq_len, hidden_dim2)
        latent_space = self.latent_space(enc_out2)
        # latent_space = self.relu(latent_space)

        # Decoder
        dec_out1, _ = self.decoder_lstm1(latent_space)
        # dec_out1 = self.relu(dec_out1)
        dec_out1 = self.dropout(dec_out1)

        dec_out2, _ = self.decoder_lstm2(dec_out1)
        # dec_out2 = self.relu(dec_out2)
        dec_out2 = self.dropout(dec_out2)

        output = self.output_layer(dec_out2)

        return output
