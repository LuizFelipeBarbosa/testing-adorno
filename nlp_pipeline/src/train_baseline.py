"""Stage 5a: Baseline classifiers (TF-IDF + Logistic Regression / SVM).

Trains a multi-label classifier using OneVsRest wrapping with class-weighted
estimators. Supports both Logistic Regression and Linear SVM.
"""

from __future__ import annotations

import pickle
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.multiclass import OneVsRestClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

from src.utils.io_utils import load_yaml, ensure_dir, project_root
from src.utils.logging_utils import get_logger
from src.utils.seed import set_global_seed

logger = get_logger(__name__)

CRITIQUE_LABELS = [
    "STANDARDIZATION",
    "PSEUDO_INDIVIDUALIZATION",
    "COMMODIFICATION_MARKET_LOGIC",
    "REGRESSIVE_LISTENING",
    "AFFECTIVE_PREPACKAGING",
    "FORMAL_RESISTANCE",
]


def _build_label_matrix(
    df: pd.DataFrame,
    label_cols: list[str] | None = None,
) -> np.ndarray:
    """Build a binary label matrix from weak label columns."""
    cols = label_cols or [f"weak_{lbl}" for lbl in CRITIQUE_LABELS]
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing label columns: {missing}")
    return df[cols].astype(int).values


def _split_data(
    df: pd.DataFrame,
    y: np.ndarray,
    config: dict,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    """Deterministic train/val/test split."""
    seed = config.get("seed", 42)
    train_ratio = config["data"]["train_ratio"]
    val_ratio = config["data"]["val_ratio"]

    # First split: train+val vs test
    test_ratio = 1.0 - train_ratio - val_ratio
    df_trainval, df_test, y_trainval, y_test = train_test_split(
        df, y, test_size=test_ratio, random_state=seed
    )

    # Second split: train vs val
    val_of_trainval = val_ratio / (train_ratio + val_ratio)
    df_train, df_val, y_train, y_val = train_test_split(
        df_trainval, y_trainval, test_size=val_of_trainval, random_state=seed
    )

    logger.info(
        "Split: train=%d, val=%d, test=%d",
        len(df_train),
        len(df_val),
        len(df_test),
    )
    return df_train, df_val, df_test, y_train, y_val, y_test


def train_tfidf_logreg(
    df: pd.DataFrame,
    config_path: str | Path | None = None,
    text_col: str = "clean_text",
    model_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Train TF-IDF + OneVsRest Logistic Regression.

    Returns a dict with the pipeline, vectorizer, metrics, and split indices.
    """
    config = load_yaml(config_path or project_root() / "configs" / "model_config.yaml")
    set_global_seed(config.get("seed", 42))

    y = _build_label_matrix(df)
    df_train, df_val, df_test, y_train, y_val, y_test = _split_data(df, y, config)

    tfidf_cfg = config["baseline"]["tfidf"]
    lr_cfg = config["baseline"]["logistic_regression"]

    vectorizer = TfidfVectorizer(
        max_features=tfidf_cfg["max_features"],
        ngram_range=tuple(tfidf_cfg["ngram_range"]),
        min_df=tfidf_cfg["min_df"],
        max_df=tfidf_cfg["max_df"],
        sublinear_tf=tfidf_cfg["sublinear_tf"],
    )

    X_train = vectorizer.fit_transform(df_train[text_col].fillna(""))
    X_val = vectorizer.transform(df_val[text_col].fillna(""))
    X_test = vectorizer.transform(df_test[text_col].fillna(""))

    estimator = LogisticRegression(
        C=lr_cfg["C"],
        max_iter=lr_cfg["max_iter"],
        solver=lr_cfg["solver"],
        class_weight=lr_cfg["class_weight"],
        random_state=config.get("seed", 42),
    )
    classifier = OneVsRestClassifier(estimator, n_jobs=-1)
    classifier.fit(X_train, y_train)

    # Predictions
    y_train_pred = classifier.predict(X_train)
    y_val_pred = classifier.predict(X_val)
    y_test_pred = classifier.predict(X_test)

    # Probabilities
    y_val_proba = classifier.predict_proba(X_val)
    y_test_proba = classifier.predict_proba(X_test)

    # Save model
    out_dir = Path(model_dir or project_root() / "models" / "baseline_logreg")
    ensure_dir(out_dir)

    with open(out_dir / "vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)
    with open(out_dir / "classifier.pkl", "wb") as f:
        pickle.dump(classifier, f)

    logger.info("Saved baseline model to %s", out_dir)

    return {
        "model_type": "tfidf_logreg",
        "vectorizer": vectorizer,
        "classifier": classifier,
        "splits": {
            "train_idx": df_train.index.tolist(),
            "val_idx": df_val.index.tolist(),
            "test_idx": df_test.index.tolist(),
        },
        "predictions": {
            "y_train": y_train,
            "y_val": y_val,
            "y_test": y_test,
            "y_train_pred": y_train_pred,
            "y_val_pred": y_val_pred,
            "y_test_pred": y_test_pred,
            "y_val_proba": y_val_proba,
            "y_test_proba": y_test_proba,
        },
        "feature_names": vectorizer.get_feature_names_out().tolist(),
        "model_dir": str(out_dir),
    }


def train_tfidf_svm(
    df: pd.DataFrame,
    config_path: str | Path | None = None,
    text_col: str = "clean_text",
    model_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Train TF-IDF + OneVsRest Linear SVM (with calibration for probabilities).

    Returns a dict with the pipeline, vectorizer, metrics, and split indices.
    """
    config = load_yaml(config_path or project_root() / "configs" / "model_config.yaml")
    set_global_seed(config.get("seed", 42))

    y = _build_label_matrix(df)
    df_train, df_val, df_test, y_train, y_val, y_test = _split_data(df, y, config)

    tfidf_cfg = config["baseline"]["tfidf"]
    svm_cfg = config["baseline"]["svm"]

    vectorizer = TfidfVectorizer(
        max_features=tfidf_cfg["max_features"],
        ngram_range=tuple(tfidf_cfg["ngram_range"]),
        min_df=tfidf_cfg["min_df"],
        max_df=tfidf_cfg["max_df"],
        sublinear_tf=tfidf_cfg["sublinear_tf"],
    )

    X_train = vectorizer.fit_transform(df_train[text_col].fillna(""))
    X_val = vectorizer.transform(df_val[text_col].fillna(""))
    X_test = vectorizer.transform(df_test[text_col].fillna(""))

    # Calibrate SVM for probability estimates
    base_svm = LinearSVC(
        C=svm_cfg["C"],
        class_weight=svm_cfg["class_weight"],
        random_state=config.get("seed", 42),
        max_iter=2000,
    )
    calibrated = CalibratedClassifierCV(base_svm, cv=3)
    classifier = OneVsRestClassifier(calibrated, n_jobs=-1)
    classifier.fit(X_train, y_train)

    y_val_pred = classifier.predict(X_val)
    y_test_pred = classifier.predict(X_test)
    y_val_proba = classifier.predict_proba(X_val)
    y_test_proba = classifier.predict_proba(X_test)

    out_dir = Path(model_dir or project_root() / "models" / "baseline_svm")
    ensure_dir(out_dir)

    with open(out_dir / "vectorizer.pkl", "wb") as f:
        pickle.dump(vectorizer, f)
    with open(out_dir / "classifier.pkl", "wb") as f:
        pickle.dump(classifier, f)

    logger.info("Saved SVM model to %s", out_dir)

    return {
        "model_type": "tfidf_svm",
        "vectorizer": vectorizer,
        "classifier": classifier,
        "splits": {
            "train_idx": df_train.index.tolist(),
            "val_idx": df_val.index.tolist(),
            "test_idx": df_test.index.tolist(),
        },
        "predictions": {
            "y_train": y_train,
            "y_val": y_val,
            "y_test": y_test,
            "y_val_pred": y_val_pred,
            "y_test_pred": y_test_pred,
            "y_val_proba": y_val_proba,
            "y_test_proba": y_test_proba,
        },
        "model_dir": str(out_dir),
    }


def load_baseline_model(
    model_dir: str | Path,
) -> tuple[TfidfVectorizer, OneVsRestClassifier]:
    """Load a saved baseline model (vectorizer + classifier)."""
    model_dir = Path(model_dir)
    with open(model_dir / "vectorizer.pkl", "rb") as f:
        vectorizer = pickle.load(f)
    with open(model_dir / "classifier.pkl", "rb") as f:
        classifier = pickle.load(f)
    return vectorizer, classifier
