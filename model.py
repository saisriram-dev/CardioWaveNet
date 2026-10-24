from tensorflow import keras
from tensorflow.keras import layers
from config import IMG_SIZE, CLASSES


def build_model():
    model = keras.Sequential(
        [
            keras.Input(shape=(IMG_SIZE, IMG_SIZE, 1)),
            layers.Rescaling(1.0 / 255),  # pixels 0-255 -> 0-1
            # Block 1: edges / local energy changes          -> 64x64x16
            layers.Conv2D(16, 3, padding="same", activation="relu"),
            layers.BatchNormalization(),
            layers.MaxPooling2D(),
            # Block 2: wave segments                          -> 32x32x32
            layers.Conv2D(32, 3, padding="same", activation="relu"),
            layers.BatchNormalization(),
            layers.MaxPooling2D(),
            # Block 3: QRS width, P/T wave patterns           -> 16x16x64
            layers.Conv2D(64, 3, padding="same", activation="relu"),
            layers.BatchNormalization(),
            layers.MaxPooling2D(),
            # Block 4: whole-beat patterns                    -> 16x16x128
            layers.Conv2D(128, 3, padding="same", activation="relu"),
            layers.BatchNormalization(),
            layers.GlobalAveragePooling2D(),  # -> 128 numbers
            # Classifier head
            layers.Dropout(0.4),
            layers.Dense(64, activation="relu"),
            layers.Dense(len(CLASSES), activation="softmax"),
        ],
        name="CardioWaveNet",
    )

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",  # labels are integers 0..4
        metrics=["accuracy"],
    )
    return model


if __name__ == "__main__":
    build_model().summary()  # run `python model.py` to see layers + param count
