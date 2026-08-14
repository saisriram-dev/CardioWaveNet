import os
import wfdb
import pywt
import numpy as np
import cv2

# --- UPDATED PATH HERE ---
BASE_DIR = r"C:/Users/P SAI SRI RAM/OneDrive/Desktop/Projects/ECG_Project/"
DATA_DIR = os.path.join(BASE_DIR, "mitbih_data")
IMAGE_DIR = os.path.join(BASE_DIR, "scalograms")

# AAMI EC57 Categories Mapping
AAMI_MAPPING = {
    'N': 'N', 'L': 'N', 'R': 'N', 'e': 'N', 'j': 'N',
    'A': 'S', 'a': 'S', 'J': 'S', 'S': 'S',
    'V': 'V', 'E': 'V', 'F': 'F', '/': 'Q', 'f': 'Q', 'Q': 'Q'
}

# Create folders for the images
for c in ['N', 'S', 'V', 'F', 'Q']:
    os.makedirs(os.path.join(IMAGE_DIR, c), exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

print("Downloading MIT-BIH Data...")
records = ['100', '119', '200', '214'] # Subset for mid-review
wfdb.dl_database('mitdb', DATA_DIR, records=records)

print("Extracting beats and creating images...")
for record in records:
    record_path = os.path.join(DATA_DIR, record)
    sig, _ = wfdb.rdsamp(record_path, channels=[0]) # Read ECG signal
    ann = wfdb.rdann(record_path, 'atr')            # Read annotations (R-peaks)
    
    sig = sig.flatten()
    
    for i in range(1, len(ann.sample) - 1):
        sym = ann.symbol[i]
        if sym in AAMI_MAPPING:
            aami_class = AAMI_MAPPING[sym]
            peak = ann.sample[i]
            
            # Segment beat (100 samples before, 150 after)
            start, end = peak - 100, peak + 150
            
            if start > 0 and end < len(sig):
                beat = sig[start:end]
                
                # Apply Continuous Wavelet Transform (CWT)
                coef, _ = pywt.cwt(beat, np.arange(1, 64), 'morl')
                img = cv2.normalize(np.abs(coef), None, 0, 255, cv2.NORM_MINMAX)
                img = cv2.resize(np.uint8(img), (128, 128))
                
                img_path = os.path.join(IMAGE_DIR, aami_class, f"{record}_{peak}.png")
                cv2.imwrite(img_path, img)

print("Done! Check the 'scalograms' folder inside CardioWaveNet.")
