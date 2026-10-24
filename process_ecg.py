import os
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
import numpy as np
import pywt
import requests
import wfdb

from config import DATA_DIR, IMAGE_DIR, CLASSES, IMG_SIZE

# PhysioNet's official AWS open-data mirror serves identical files, much faster.
# physionet.org is only used as a per-file fallback.
MIRRORS = [
    "https://physionet-open.s3.amazonaws.com/mitdb/1.0.0/",
    "https://physionet.org/files/mitdb/1.0.0/",
]

# All 48 MIT-BIH records (hard-coded so we never query the slow server for the list)
RECORDS = [
    "100", "101", "102", "103", "104", "105", "106", "107", "108", "109",
    "111", "112", "113", "114", "115", "116", "117", "118", "119",
    "121", "122", "123", "124",
    "200", "201", "202", "203", "205", "207", "208", "209", "210",
    "212", "213", "214", "215", "217", "219", "220", "221", "222", "223",
    "228", "230", "231", "232", "233", "234",
]
EXTENSIONS = [".hea", ".dat", ".atr"]
DAT_SIZE = 1_950_000  # every MIT-BIH .dat: 650,000 samples x 2 channels x 12 bits

# AAMI EC57 Categories Mapping
AAMI_MAPPING = {
    "N": "N", "L": "N", "R": "N", "e": "N", "j": "N",
    "A": "S", "a": "S", "J": "S", "S": "S",
    "V": "V", "E": "V",
    "F": "F",
    "/": "Q", "f": "Q", "Q": "Q",
}
N_KEEP_EVERY = 10          # keep 1 of every 10 normal beats (N is ~80% of MIT-BIH)
BEFORE, AFTER = 100, 150   # samples around the R-peak (278 ms before, 417 ms after)
SCALES = np.arange(1, 64)  # CWT scales


def is_complete(path):
    """True if the file exists and is not a half-finished download."""
    if not os.path.exists(path):
        return False
    size = os.path.getsize(path)
    return size == DAT_SIZE if path.endswith(".dat") else size > 0


def download_file(fname):
    dest = os.path.join(DATA_DIR, fname)
    if is_complete(dest):
        return fname, "already downloaded"
    error = None
    for base in MIRRORS:
        try:
            r = requests.get(base + fname, timeout=(10, 120))
            r.raise_for_status()
            with open(dest + ".part", "wb") as f:
                f.write(r.content)
            os.replace(dest + ".part", dest)  # only complete files get the real name
            return fname, "ok from " + base.split("/")[2]
        except requests.RequestException as e:
            error = e
    return fname, f"FAILED ({error})"


def download_mitdb():
    os.makedirs(DATA_DIR, exist_ok=True)
    files = [rec + ext for rec in RECORDS for ext in EXTENSIONS]
    print(f"Downloading {len(files)} files (~95 MB) with 8 parallel connections...")
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = [pool.submit(download_file, f) for f in files]
        for i, fut in enumerate(as_completed(futures), 1):
            fname, status = fut.result()
            print(f"[{i}/{len(files)}] {fname}: {status}")


def available_records():
    ok = [
        rec for rec in RECORDS
        if all(is_complete(os.path.join(DATA_DIR, rec + ext)) for ext in EXTENSIONS)
    ]
    missing = [rec for rec in RECORDS if rec not in ok]
    print(f"{len(ok)}/48 records complete.")
    if missing:
        print("Missing (re-run this script later to fetch them):", missing)
    return ok


def beat_to_scalogram(beat):
    coef, _ = pywt.cwt(beat, SCALES, "morl")  # Continuous Wavelet Transform
    img = cv2.normalize(np.abs(coef), None, 0, 255, cv2.NORM_MINMAX)
    return cv2.resize(np.uint8(img), (IMG_SIZE, IMG_SIZE))


def main():
    download_mitdb()
    records = available_records()
    if not records:
        raise SystemExit("No complete records found - check your internet connection.")

    # Start fresh so images from the old 4-record run don't mix in
    shutil.rmtree(IMAGE_DIR, ignore_errors=True)
    for c in CLASSES:
        os.makedirs(os.path.join(IMAGE_DIR, c), exist_ok=True)

    print("Extracting beats and creating scalograms...")
    counts = dict.fromkeys(CLASSES, 0)
    n_counter = 0
    for record in records:
        record_path = os.path.join(DATA_DIR, record)
        sig, _ = wfdb.rdsamp(record_path, channels=[0])  # ECG signal, channel 0
        ann = wfdb.rdann(record_path, "atr")  # beat annotations (R-peaks)
        sig = sig.flatten()

        for i in range(1, len(ann.sample) - 1):
            sym = ann.symbol[i]
            if sym not in AAMI_MAPPING:
                continue
            aami_class = AAMI_MAPPING[sym]

            if aami_class == "N":
                n_counter += 1
                if n_counter % N_KEEP_EVERY != 0:
                    continue

            peak = ann.sample[i]
            start, end = peak - BEFORE, peak + AFTER
            if start > 0 and end < len(sig):
                img = beat_to_scalogram(sig[start:end])
                img_path = os.path.join(IMAGE_DIR, aami_class, f"{record}_{peak}.png")
                cv2.imwrite(img_path, img)
                counts[aami_class] += 1

        print(f"Record {record} done")

    print("Images per class:", counts)
    print(f"Done! Scalograms saved in: {IMAGE_DIR}")


if __name__ == "__main__":
    main()
