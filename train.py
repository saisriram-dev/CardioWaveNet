import os
import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.utils.class_weight import compute_class_weight
from tensorflow import keras
from config import OUTPUT_DIR, MODEL_PATH, CLASSES, SEED
from dataset import get_splits
from model import build_model

keras.utils.set_random_seed(SEED)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 1. Data
(X_train, y_train), (X_val, y_val), _ = get_splits()
print("Train images per class:", dict(zip(CLASSES, np.bincount(y_train))))
print("Val images per class:  ", dict(zip(CLASSES, np.bincount(y_val))))

# 2. Class weights: rare classes get a bigger weight in the loss
weights = compute_class_weight("balanced", classes=np.arange(len(CLASSES)), y=y_train)
class_weight = dict(enumerate(weights))
print("Class weights:", {CLASSES[k]: round(v, 2) for k, v in class_weight.items()})

# 3. Model
model = build_model()
model.summary()

# 4. Train (stops early when validation loss stops improving)
callbacks = [
    keras.callbacks.EarlyStopping(
        monitor="val_loss", patience=5, restore_best_weights=True
    ),
    keras.callbacks.ModelCheckpoint(
        MODEL_PATH, monitor="val_loss", save_best_only=True
    ),
]
history = model.fit(
    X_train,
    y_train,
    validation_data=(X_val, y_val),
    epochs=30,
    batch_size=64,
    class_weight=class_weight,
    callbacks=callbacks,
)

# 5. Save training curves
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
ax1.plot(history.history["accuracy"], label="train")
ax1.plot(history.history["val_accuracy"], label="validation")
ax1.set_title("Accuracy")
ax1.set_xlabel("Epoch")
ax1.legend()
ax2.plot(history.history["loss"], label="train")
ax2.plot(history.history["val_loss"], label="validation")
ax2.set_title("Loss")
ax2.set_xlabel("Epoch")
ax2.legend()
fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "training_curves.png"), dpi=150)

print(f"Model saved to {MODEL_PATH}")
