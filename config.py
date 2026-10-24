import os

# Where the raw data and scalograms live (outside the git repo)
BASE_DIR = r"C:/Users/P SAI SRI RAM/OneDrive/Desktop/Projects/ECG_Project/"
DATA_DIR = os.path.join(BASE_DIR, "mitbih_data")
IMAGE_DIR = os.path.join(BASE_DIR, "scalograms")

# Where model + results are saved (inside CardioWaveNet)
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(PROJECT_DIR, "outputs")
MODEL_PATH = os.path.join(OUTPUT_DIR, "cardiowavenet.keras")

CLASSES = ["N", "S", "V", "F", "Q"]  # label 0..4 in this order
IMG_SIZE = 128
SEED = 42
