import os
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
)
from tensorflow import keras
from config import OUTPUT_DIR, MODEL_PATH, CLASSES
from dataset import get_splits

# Same seed -> exactly the same test set the model never saw during training
_, _, (X_test, y_test) = get_splits()
model = keras.models.load_model(MODEL_PATH)

probs = model.predict(X_test, batch_size=128)
y_pred = probs.argmax(axis=1)

# Per-class precision, recall, F1
report = classification_report(
    y_test,
    y_pred,
    labels=list(range(len(CLASSES))),
    target_names=CLASSES,
    digits=3,
    zero_division=0,
)
print(report)
with open(os.path.join(OUTPUT_DIR, "classification_report.txt"), "w") as f:
    f.write(report)

# Confusion matrix
cm = confusion_matrix(y_test, y_pred, labels=list(range(len(CLASSES))))
fig, ax = plt.subplots(figsize=(6, 5))
ConfusionMatrixDisplay(cm, display_labels=CLASSES).plot(
    ax=ax, cmap="Blues", colorbar=False
)
ax.set_title("CardioWaveNet - Test Set Confusion Matrix")
fig.tight_layout()
fig.savefig(os.path.join(OUTPUT_DIR, "confusion_matrix.png"), dpi=150)
print("Saved confusion_matrix.png and classification_report.txt in outputs/")
