"""
src/train_model.py
═══════════════════════════════════════════════════════════════
FASAL DOCTOR — Phase 2
EfficientNet-B0 Training Script (per-crop)

Usage:
    python src/train_model.py --crop wheat
    python src/train_model.py --crop cotton
    python src/train_model.py --crop rice
    python src/train_model.py --crop sugarcane
    python src/train_model.py --crop maize
    python src/train_model.py --crop potato
    python src/train_model.py --crop tomato

Outputs (saved to models/):
    {crop}_best.h5          ← best checkpoint during Phase 1
    {crop}_final.h5         ← best checkpoint during Phase 2 (fine-tune)
    {crop}_classes.json     ← ordered list of class names
    {crop}_report.txt       ← sklearn classification report
    {crop}_history.json     ← training curves (accuracy/loss per epoch)
═══════════════════════════════════════════════════════════════
"""

import argparse
import json
import os
import shutil
import time
from pathlib import Path

import numpy as np

# ── TensorFlow ────────────────────────────────────────────────
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"   # suppress verbose TF logs
import tensorflow as tf
from tensorflow.keras.applications import EfficientNetB0
from tensorflow.keras.applications.efficientnet import preprocess_input as efficientnet_preprocess
from tensorflow.keras.layers import (
    GlobalAveragePooling2D, Dense, Dropout, BatchNormalization
)
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import (
    ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
)
from tensorflow.keras.preprocessing.image import ImageDataGenerator

from sklearn.metrics import classification_report, confusion_matrix
from sklearn.utils.class_weight import compute_class_weight

# ─────────────────────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────────────────────
IMAGE_SIZE    = (224, 224)
BATCH_SIZE    = 32
PHASE1_EPOCHS = 15     # frozen backbone — feature extraction
PHASE2_EPOCHS = 15     # unfreeze top layers — fine-tuning
PHASE1_LR     = 1e-3
PHASE2_LR     = 1e-4
UNFREEZE_LAST = 30     # number of EfficientNet layers to unfreeze

BASE_DIR      = Path(__file__).resolve().parent.parent
DATA_DIR      = BASE_DIR / "data" / "images"
MODELS_DIR    = BASE_DIR / "models"

SPLIT_RATIOS  = (0.70, 0.15, 0.15)   # train / val / test

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def split_dataset(crop_dir: Path, tmp_dir: Path, ratios=(0.70, 0.15, 0.15)):
    """
    If the crop folder is flat (class dirs directly under crop_dir),
    split images into train/val/test under tmp_dir.
    If it already has train/val/test folders, copy them as-is.
    Returns (train_dir, val_dir, test_dir, class_names).
    """
    children = [d for d in crop_dir.iterdir() if d.is_dir()]
    SPLIT_KEYWORDS = {"train","training","val","validation","valid","test","testing"}

    has_splits = any(c.name.lower() in SPLIT_KEYWORDS for c in children)

    if has_splits:
        # Already split — find the directories
        train_dir = val_dir = test_dir = None
        for c in children:
            nl = c.name.lower()
            if "train" in nl: train_dir = c
            elif "val" in nl:  val_dir   = c
            elif "test" in nl: test_dir  = c
        # Class names from training folder
        class_names = sorted([d.name for d in train_dir.iterdir() if d.is_dir()])
        return train_dir, val_dir, test_dir, class_names

    # Flat layout — manual split
    import random, math
    random.seed(42)

    train_r, val_r, _ = ratios
    train_dir = tmp_dir / "train"
    val_dir   = tmp_dir / "val"
    test_dir  = tmp_dir / "test"

    IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp"}
    class_names = sorted([d.name for d in children])

    for split in [train_dir, val_dir, test_dir]:
        split.mkdir(parents=True, exist_ok=True)

    for cls_dir in children:
        images = [f for f in cls_dir.iterdir()
                  if f.is_file() and f.suffix.lower() in IMG_EXTS]
        random.shuffle(images)
        n      = len(images)
        n_tr   = math.floor(n * train_r)
        n_val  = math.floor(n * val_r)

        splits_data = {
            "train": images[:n_tr],
            "val":   images[n_tr : n_tr + n_val],
            "test":  images[n_tr + n_val :],
        }
        for split_name, files in splits_data.items():
            dst_cls = tmp_dir / split_name / cls_dir.name
            dst_cls.mkdir(parents=True, exist_ok=True)
            for f in files:
                shutil.copy2(f, dst_cls / f.name)

    return train_dir, val_dir, test_dir, class_names


def build_model(num_classes: int) -> tuple[Model, object]:
    """Build EfficientNetB0 with custom head. Returns (model, base_model)."""
    base_model = EfficientNetB0(
        weights="imagenet",
        include_top=False,
        input_shape=(224, 224, 3),
    )
    base_model.trainable = False   # Phase 1: frozen

    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = BatchNormalization()(x)
    x = Dense(256, activation="relu")(x)
    x = Dropout(0.4)(x)
    x = Dense(128, activation="relu")(x)
    x = Dropout(0.3)(x)
    output = Dense(num_classes, activation="softmax")(x)

    model = Model(inputs=base_model.input, outputs=output)
    return model, base_model


def make_generators(train_dir, val_dir, test_dir):
    """Return (train_gen, val_gen, test_gen)."""
    # IMPORTANT: EfficientNetB0 includes its own internal Rescaling layer
    # and expects raw pixel values in [0, 255]. Using rescale=1./255 causes
    # double-normalisation → model gets near-zero inputs → mode collapse.
    # Use preprocessing_function=efficientnet_preprocess instead.
    train_datagen = ImageDataGenerator(
        preprocessing_function=efficientnet_preprocess,
        rotation_range=25,
        width_shift_range=0.2,
        height_shift_range=0.2,
        horizontal_flip=True,
        vertical_flip=False,
        zoom_range=0.25,
        brightness_range=[0.7, 1.3],
        shear_range=0.15,
        fill_mode="nearest",
    )
    val_datagen = ImageDataGenerator(preprocessing_function=efficientnet_preprocess)

    train_gen = train_datagen.flow_from_directory(
        train_dir,
        target_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        shuffle=True,
    )
    val_gen = val_datagen.flow_from_directory(
        val_dir,
        target_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        shuffle=False,
    )
    test_gen = val_datagen.flow_from_directory(
        test_dir,
        target_size=IMAGE_SIZE,
        batch_size=BATCH_SIZE,
        class_mode="categorical",
        shuffle=False,
    )
    return train_gen, val_gen, test_gen


def history_to_dict(h1, h2) -> dict:
    """Merge two Keras History objects into a serialisable dict."""
    def safe(hist, key):
        return [float(v) for v in hist.history.get(key, [])]

    return {
        "phase1": {
            "accuracy":     safe(h1, "accuracy"),
            "val_accuracy": safe(h1, "val_accuracy"),
            "loss":         safe(h1, "loss"),
            "val_loss":     safe(h1, "val_loss"),
        },
        "phase2": {
            "accuracy":     safe(h2, "accuracy"),
            "val_accuracy": safe(h2, "val_accuracy"),
            "loss":         safe(h2, "loss"),
            "val_loss":     safe(h2, "val_loss"),
        },
    }


def best_val_acc(history) -> float:
    vals = history.history.get("val_accuracy", [0.0])
    return float(max(vals)) if vals else 0.0


def compute_class_weights(train_gen) -> dict:
    """
    Compute balanced class weights from a Keras DirectoryIterator.
    Returns a dict {class_index: weight} ready for model.fit(class_weight=...).
    Rare classes get higher weights so the model is penalised more for
    misclassifying them — the correct fix for imbalanced datasets.
    """
    labels = train_gen.classes
    class_indices = np.unique(labels)
    weights = compute_class_weight(
        class_weight="balanced",
        classes=class_indices,
        y=labels,
    )
    cw = {int(i): float(w) for i, w in zip(class_indices, weights)}
    print("  ▸ Class weights:")
    idx_to_name = {v: k for k, v in train_gen.class_indices.items()}
    for idx, w in sorted(cw.items()):
        bar = "▓" * min(int(w * 10), 30)
        print(f"      [{idx}] {idx_to_name.get(idx, idx):<30} weight={w:.3f}  {bar}")
    return cw


# ─────────────────────────────────────────────────────────────
# MAIN TRAINING FUNCTION
# ─────────────────────────────────────────────────────────────

def train(crop: str, use_class_weights: bool = True):
    crop = crop.lower()
    crop_dir = DATA_DIR / crop

    if not crop_dir.exists():
        print(f"\n❌ ERROR: data/images/{crop}/ not found.")
        print(f"   Run organize_images.py first.\n")
        return

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # ── Temporary split directory ─────────────────────────────
    tmp_dir = BASE_DIR / "data" / "_tmp_split" / crop
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)

    print(f"\n{'═'*50}")
    print(f"  FASAL DOCTOR — TRAINING: {crop.upper()}")
    print(f"{'═'*50}")
    print(f"  TensorFlow : {tf.__version__}")
    gpus = tf.config.list_physical_devices("GPU")
    print(f"  GPU(s)     : {gpus if gpus else 'None — CPU mode'}")
    print(f"  Crop dir   : {crop_dir}")
    print()

    # ── Split & generators ────────────────────────────────────
    print("  ▸ Splitting dataset...")
    train_dir, val_dir, test_dir, class_names = split_dataset(
        crop_dir, tmp_dir, SPLIT_RATIOS
    )
    num_classes = len(class_names)
    print(f"  ▸ Classes ({num_classes}): {class_names}")

    train_gen, val_gen, test_gen = make_generators(train_dir, val_dir, test_dir)
    print(f"  ▸ Train batches : {len(train_gen)}")
    print(f"  ▸ Val   batches : {len(val_gen)}")
    print(f"  ▸ Test  batches : {len(test_gen)}")
    print()

    # ── Class weights (fix imbalance) ─────────────────────────
    class_weight_dict = None
    if use_class_weights:
        print("  ▸ Computing class weights for imbalance correction...")
        class_weight_dict = compute_class_weights(train_gen)
        print()

    # ── Build model ───────────────────────────────────────────
    model, base_model = build_model(num_classes)
    print(f"  ▸ Model parameters: {model.count_params():,}")
    print()

    # ══ PHASE 1: Feature Extraction (frozen backbone) ═════════
    print(f"{'─'*50}")
    print("  PHASE 1 — Feature Extraction (backbone frozen)")
    print(f"  Epochs: {PHASE1_EPOCHS}  |  LR: {PHASE1_LR}")
    print(f"{'─'*50}")

    model.compile(
        optimizer=Adam(PHASE1_LR),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks_p1 = [
        EarlyStopping(patience=5, restore_best_weights=True, verbose=1),
        ReduceLROnPlateau(factor=0.3, patience=3, verbose=1, min_lr=1e-6),
        ModelCheckpoint(
            str(MODELS_DIR / f"{crop}_best.h5"),
            save_best_only=True,
            monitor="val_accuracy",
            verbose=1,
        ),
    ]

    t0 = time.time()
    history1 = model.fit(
        train_gen,
        epochs=PHASE1_EPOCHS,
        validation_data=val_gen,
        callbacks=callbacks_p1,
        class_weight=class_weight_dict,
        verbose=1,
    )
    p1_best = best_val_acc(history1)
    print(f"\n  Phase 1 best val_accuracy: {p1_best:.4f}")

    # ══ PHASE 2: Fine-tuning (unfreeze top layers) ════════════
    print(f"\n{'─'*50}")
    print(f"  PHASE 2 — Fine-tuning (top {UNFREEZE_LAST} layers unfrozen)")
    print(f"  Epochs: {PHASE2_EPOCHS}  |  LR: {PHASE2_LR}")
    print(f"{'─'*50}")

    for layer in base_model.layers[-UNFREEZE_LAST:]:
        layer.trainable = True

    model.compile(
        optimizer=Adam(PHASE2_LR),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )

    callbacks_p2 = [
        EarlyStopping(patience=7, restore_best_weights=True, verbose=1),
        ReduceLROnPlateau(factor=0.2, patience=4, verbose=1, min_lr=1e-7),
        ModelCheckpoint(
            str(MODELS_DIR / f"{crop}_final.h5"),
            save_best_only=True,
            monitor="val_accuracy",
            verbose=1,
        ),
    ]

    history2 = model.fit(
        train_gen,
        epochs=PHASE2_EPOCHS,
        validation_data=val_gen,
        callbacks=callbacks_p2,
        class_weight=class_weight_dict,
        verbose=1,
    )
    p2_best = best_val_acc(history2)
    elapsed = time.time() - t0
    print(f"\n  Phase 2 best val_accuracy: {p2_best:.4f}")

    # ══ EVALUATION ════════════════════════════════════════════
    print(f"\n{'─'*50}")
    print("  EVALUATION on test set")
    print(f"{'─'*50}")

    test_gen.reset()
    loss, accuracy = model.evaluate(test_gen, verbose=0)

    test_gen.reset()
    y_pred_probs = model.predict(test_gen, verbose=0)
    y_pred = y_pred_probs.argmax(axis=1)
    y_true = test_gen.classes

    report_str = classification_report(
        y_true, y_pred,
        target_names=class_names,
        zero_division=0,
    )
    cm = confusion_matrix(y_true, y_pred)

    # ══ SAVE OUTPUTS ══════════════════════════════════════════
    # 1. Class list
    classes_path = MODELS_DIR / f"{crop}_classes.json"
    with open(classes_path, "w", encoding="utf-8") as f:
        json.dump(class_names, f, indent=2)

    # 2. Classification report
    report_path = MODELS_DIR / f"{crop}_report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"CROP: {crop.upper()}\n")
        f.write(f"Phase 1 best val_accuracy: {p1_best:.4f}\n")
        f.write(f"Phase 2 best val_accuracy: {p2_best:.4f}\n")
        f.write(f"Test accuracy : {accuracy:.4f}\n")
        f.write(f"Test loss     : {loss:.4f}\n\n")
        f.write(report_str)
        f.write(f"\nConfusion Matrix:\n")
        f.write(np.array2string(cm))

    # 3. Training history
    history_path = MODELS_DIR / f"{crop}_history.json"
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump(history_to_dict(history1, history2), f, indent=2)

    # ── Clean up tmp split dir ────────────────────────────────
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)

    # ══ FINAL SUMMARY ═════════════════════════════════════════
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    print(f"\n{'═'*50}")
    print(f"  TRAINING COMPLETE — {crop.upper()}")
    print(f"{'═'*50}")
    print(f"  Classes: {num_classes}")
    for i, cls in enumerate(class_names):
        print(f"    {i}: {cls}")
    print()
    print(f"  Phase 1 best val_accuracy : {p1_best:.4f}  ({p1_best*100:.1f}%)")
    print(f"  Phase 2 best val_accuracy : {p2_best:.4f}  ({p2_best*100:.1f}%)")
    print()
    print(f"  TEST RESULTS:")
    print(f"    Overall Accuracy : {accuracy*100:.2f}%")
    print(f"    Overall Loss     : {loss:.4f}")
    print()
    print(f"  {report_str}")
    print()
    print(f"  Model saved    : models/{crop}_final.h5")
    print(f"  Classes saved  : models/{crop}_classes.json")
    print(f"  Report saved   : models/{crop}_report.txt")
    print(f"  History saved  : models/{crop}_history.json")
    print(f"  Training time  : {mins}m {secs}s")

    # Accuracy gate
    threshold = 80.0
    if accuracy * 100 >= threshold:
        print(f"\n  ✅ PASSED accuracy gate ({accuracy*100:.1f}% ≥ {threshold}%)")
    else:
        print(f"\n  ⚠  BELOW accuracy gate ({accuracy*100:.1f}% < {threshold}%)")
        print(f"     Suggestions:")
        print(f"       • Increase augmentation strength")
        print(f"       • Add more training epochs (edit PHASE1/2_EPOCHS)")
        print(f"       • Check class images are correctly labelled")
        print(f"       • Flag crop as 'beta' in UI with warning")

    print(f"{'═'*50}\n")


# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="FASAL DOCTOR — Train EfficientNetB0 for a crop"
    )
    parser.add_argument(
        "--crop",
        required=True,
        choices=["wheat","cotton","rice","sugarcane","maize","potato","tomato"],
        help="Crop to train (must match folder in data/images/)",
    )
    parser.add_argument(
        "--no-weights",
        action="store_true",
        default=False,
        help="Disable class weight balancing (not recommended for imbalanced crops)",
    )
    args = parser.parse_args()
    train(args.crop, use_class_weights=not args.no_weights)
