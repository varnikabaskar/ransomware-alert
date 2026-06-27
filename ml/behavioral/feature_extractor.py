import numpy as np
from typing import Any

try:
    from tensorflow.keras import Input, Model
    from tensorflow.keras.layers import Dense, Dropout, LSTM
    from tensorflow.keras.optimizers import Adam
    TF_AVAILABLE = True
except Exception:
    TF_AVAILABLE = False


class FallbackClassifier:
    def fit(self, x: np.ndarray, y: np.ndarray, validation_split: float = 0.2, epochs: int = 5, batch_size: int = 64, verbose: int = 0) -> None:
        return None


class FallbackExtractor:
    def __init__(self, latent_dim: int = 16) -> None:
        self.latent_dim = latent_dim

    def predict(self, windows: np.ndarray, verbose: int = 0) -> np.ndarray:
        mean = np.mean(windows, axis=1)
        std = np.std(windows, axis=1)
        base = np.concatenate([mean, std], axis=1)
        if base.shape[1] >= self.latent_dim:
            return base[:, : self.latent_dim].astype(np.float32)
        pad = np.zeros((base.shape[0], self.latent_dim - base.shape[1]), dtype=np.float32)
        return np.concatenate([base, pad], axis=1).astype(np.float32)


def build_lstm_extractor(sequence_length: int, feature_dim: int, latent_dim: int = 16) -> tuple[Any, Any]:
    if not TF_AVAILABLE:
        return FallbackClassifier(), FallbackExtractor(latent_dim=latent_dim)

    inputs = Input(shape=(sequence_length, feature_dim))
    x = LSTM(32, return_sequences=True)(inputs)
    x = Dropout(0.2)(x)
    x = LSTM(latent_dim, return_sequences=False, name="latent_vector")(x)
    outputs = Dense(1, activation="sigmoid")(x)

    classifier = Model(inputs, outputs)
    classifier.compile(optimizer=Adam(learning_rate=1e-3), loss="binary_crossentropy", metrics=["accuracy"])

    extractor = Model(inputs, classifier.get_layer("latent_vector").output)
    return classifier, extractor


def summarize_sequence_stats(windows: np.ndarray) -> np.ndarray:
    mean = np.mean(windows, axis=1)
    std = np.std(windows, axis=1)
    maxv = np.max(windows, axis=1)
    minv = np.min(windows, axis=1)
    return np.concatenate([mean, std, maxv, minv], axis=1).astype(np.float32)


def build_combined_features(extractor: Any, windows: np.ndarray) -> np.ndarray:
    latent = extractor.predict(windows, verbose=0)
    stats = summarize_sequence_stats(windows)
    return np.concatenate([latent, stats], axis=1).astype(np.float32)
