import os
import cv2
import numpy as np
from sklearn.model_selection import train_test_split
from config import IMAGE_DIR, CLASSES, SEED


def load_images():
    """Read every scalogram PNG. Label = index of its folder in CLASSES."""
    X, y = [], []
    for label, cls in enumerate(CLASSES):
        folder = os.path.join(IMAGE_DIR, cls)
        for fname in sorted(os.listdir(folder)):
            if fname.endswith(".png"):
                img = cv2.imread(os.path.join(folder, fname), cv2.IMREAD_GRAYSCALE)
                X.append(img)
                y.append(label)
    X = np.array(X, dtype=np.uint8)[..., np.newaxis]  # shape: (n, 128, 128, 1)
    y = np.array(y)
    return X, y


def get_splits():
    """Stratified 70% train / 15% val / 15% test. Same seed -> same split every time."""
    X, y = load_images()
    X_train, X_temp, y_train, y_temp = train_test_split(
        X, y, test_size=0.30, stratify=y, random_state=SEED
    )
    X_val, X_test, y_val, y_test = train_test_split(
        X_temp, y_temp, test_size=0.50, stratify=y_temp, random_state=SEED
    )
    return (X_train, y_train), (X_val, y_val), (X_test, y_test)
