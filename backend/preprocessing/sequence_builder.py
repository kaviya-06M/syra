from typing import Tuple
import numpy as np


class SequenceBuilder:
    """
    Converts scaled feature vectors into sliding-window
    sequences suitable for an LSTM Autoencoder.
    """

    def __init__(self, sequence_length: int = 10):

        if sequence_length <= 0:
            raise ValueError(
                "sequence_length must be greater than 0"
            )

        self.sequence_length = sequence_length

    def build(self, feature_vectors) -> np.ndarray:

        data = np.asarray(
            feature_vectors,
            dtype=np.float32
        )

        if data.ndim != 2:
            raise ValueError(
                "feature_vectors must be a 2D array"
            )

        number_of_samples = data.shape[0]

        if number_of_samples < self.sequence_length:

            return np.empty(
                (
                    0,
                    self.sequence_length,
                    data.shape[1]
                ),
                dtype=np.float32
            )

        sequences = []

        for index in range(
            number_of_samples - self.sequence_length + 1
        ):

            sequence = data[
                index:index + self.sequence_length
            ]

            sequences.append(sequence)

        return np.asarray(
            sequences,
            dtype=np.float32
        )

    def build_train_test(
        self,
        feature_vectors,
        train_ratio: float = 0.8
    ) -> Tuple[np.ndarray, np.ndarray]:

        if not 0 < train_ratio < 1:
            raise ValueError(
                "train_ratio must be between 0 and 1"
            )

        data = np.asarray(
            feature_vectors,
            dtype=np.float32
        )

        split_index = int(
            len(data) * train_ratio
        )

        train_data = data[:split_index]

        test_data = data[split_index:]

        train_sequences = self.build(
            train_data
        )

        test_sequences = self.build(
            test_data
        )

        return train_sequences, test_sequences