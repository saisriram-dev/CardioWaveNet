import os
import random
import numpy as np
import pandas as pd
import cv2
import streamlit as st
from tensorflow import keras
from config import MODEL_PATH, OUTPUT_DIR, IMAGE_DIR, CLASSES, IMG_SIZE

CLASS_INFO = {
    "N": "Normal (incl. bundle branch block)",
    "S": "Supraventricular ectopic",
    "V": "Ventricular ectopic",
    "F": "Fusion beat",
    "Q": "Paced / unclassifiable",
}

st.set_page_config(page_title="Cardio Wavenet", layout="wide")
st.title("Cardio Wavenet: ECG Beat Classifier")


@st.cache_resource
def load_model():
    return keras.models.load_model(MODEL_PATH)


def predict(img):
    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
    probs = model.predict(img[np.newaxis, :, :, np.newaxis], verbose=0)[0]
    return img, probs


model = load_model()
tab_demo, tab_perf = st.tabs(["Classify a beat", "Model performance"])

with tab_demo:
    source = st.radio(
        "Choose input",
        ["Random beat from dataset", "Upload a scalogram PNG"],
        horizontal=True,
    )
    img, true_label = None, None

    if source == "Random beat from dataset":
        st.info(
            "Random beats may come from the training set. "
            "See the 'Model performance' tab for honest test-set results."
        )
        chosen = st.selectbox(
            "Class to sample from",
            CLASSES,
            format_func=lambda c: f"{c} - {CLASS_INFO[c]}",
        )
        if st.button("Pick random beat"):
            folder = os.path.join(IMAGE_DIR, chosen)
            fname = random.choice(os.listdir(folder))
            img = cv2.imread(os.path.join(folder, fname), cv2.IMREAD_GRAYSCALE)
            true_label = chosen
            st.caption(f"File: {chosen}/{fname}")
    else:
        uploaded = st.file_uploader("Upload a scalogram", type=["png"])
        if uploaded is not None:
            img = cv2.imdecode(
                np.frombuffer(uploaded.read(), np.uint8), cv2.IMREAD_GRAYSCALE
            )

    if img is not None:
        img, probs = predict(img)
        pred = CLASSES[int(np.argmax(probs))]
        col1, col2 = st.columns(2)
        with col1:
            st.image(
                img, caption="Input scalogram (rows = scale, columns = time)", width=320
            )
        with col2:
            st.subheader(f"Prediction: {pred} ({CLASS_INFO[pred]})")
            st.write(f"Confidence: {probs.max() * 100:.1f}%")
            if true_label:
                st.write(
                    f"True label: {true_label} {'✅' if true_label == pred else '❌'}"
                )
            st.bar_chart(pd.DataFrame({"Probability": probs}, index=CLASSES))

with tab_perf:
    for fname, caption in [
        ("training_curves.png", "Training and validation curves"),
        ("confusion_matrix.png", "Confusion matrix on the test set"),
    ]:
        path = os.path.join(OUTPUT_DIR, fname)
        if os.path.exists(path):
            st.image(path, caption=caption)
        else:
            st.warning(f"{fname} not found. Run train.py and evaluate.py first.")
    report_path = os.path.join(OUTPUT_DIR, "classification_report.txt")
    if os.path.exists(report_path):
        with open(report_path) as f:
            st.code(f.read())
