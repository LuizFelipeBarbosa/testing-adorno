"""Stage 5b: Fine-tuned transformer for multi-label classification.

Uses HuggingFace Transformers + a simple multi-label head on top of a
pretrained encoder (default: distilbert-base-uncased).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd
import torch
from torch import nn
from torch.utils.data import Dataset, DataLoader
from sklearn.model_selection import train_test_split

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


class CommentDataset(Dataset):
    """PyTorch dataset for multi-label comment classification."""

    def __init__(
        self,
        texts: list[str],
        labels: np.ndarray | None,
        tokenizer,
        max_length: int = 256,
    ):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self) -> int:
        return len(self.texts)

    def __getitem__(self, idx: int) -> dict[str, torch.Tensor]:
        encoding = self.tokenizer(
            self.texts[idx],
            max_length=self.max_length,
            padding="max_length",
            truncation=True,
            return_tensors="pt",
        )
        item = {k: v.squeeze(0) for k, v in encoding.items()}
        if self.labels is not None:
            item["labels"] = torch.tensor(self.labels[idx], dtype=torch.float)
        return item


class MultiLabelClassifier(nn.Module):
    """Transformer encoder + linear head for multi-label classification."""

    def __init__(self, model_name: str, num_labels: int, dropout: float = 0.1):
        super().__init__()
        from transformers import AutoModel

        self.encoder = AutoModel.from_pretrained(model_name)
        hidden_size = self.encoder.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(hidden_size, num_labels)

    def forward(self, input_ids, attention_mask, token_type_ids=None, **kwargs):
        outputs = self.encoder(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
        )
        # Use [CLS] token representation
        cls_output = outputs.last_hidden_state[:, 0, :]
        cls_output = self.dropout(cls_output)
        logits = self.classifier(cls_output)
        return logits


def _compute_class_weights(y: np.ndarray) -> torch.Tensor:
    """Compute positive class weights for BCEWithLogitsLoss (inverse frequency)."""
    pos_counts = y.sum(axis=0)
    neg_counts = y.shape[0] - pos_counts
    # pos_weight = neg_count / max(pos_count, 1)
    weights = neg_counts / np.maximum(pos_counts, 1.0)
    # Cap extreme weights
    weights = np.clip(weights, 1.0, 50.0)
    return torch.tensor(weights, dtype=torch.float)


def train_transformer(
    df: pd.DataFrame,
    config_path: str | Path | None = None,
    text_col: str = "clean_text",
    model_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Fine-tune a transformer for multi-label classification.

    Returns dict with model path, metrics, and predictions.
    """
    from transformers import AutoTokenizer

    config = load_yaml(config_path or project_root() / "configs" / "model_config.yaml")
    set_global_seed(config.get("seed", 42))
    tf_cfg = config["transformer"]

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Using device: %s", device)

    # Build label matrix
    label_cols = [f"weak_{lbl}" for lbl in CRITIQUE_LABELS]
    y = df[label_cols].astype(int).values

    # Split
    seed = config.get("seed", 42)
    test_ratio = 1.0 - config["data"]["train_ratio"] - config["data"]["val_ratio"]
    df_trainval, df_test, y_trainval, y_test = train_test_split(
        df, y, test_size=test_ratio, random_state=seed
    )
    val_of_trainval = config["data"]["val_ratio"] / (
        config["data"]["train_ratio"] + config["data"]["val_ratio"]
    )
    df_train, df_val, y_train, y_val = train_test_split(
        df_trainval, y_trainval, test_size=val_of_trainval, random_state=seed
    )

    logger.info("Split: train=%d, val=%d, test=%d", len(df_train), len(df_val), len(df_test))

    # Tokenizer and datasets
    tokenizer = AutoTokenizer.from_pretrained(tf_cfg["model_name"])

    train_ds = CommentDataset(
        df_train[text_col].fillna("").tolist(), y_train, tokenizer, tf_cfg["max_length"]
    )
    val_ds = CommentDataset(
        df_val[text_col].fillna("").tolist(), y_val, tokenizer, tf_cfg["max_length"]
    )
    test_ds = CommentDataset(
        df_test[text_col].fillna("").tolist(), y_test, tokenizer, tf_cfg["max_length"]
    )

    train_loader = DataLoader(train_ds, batch_size=tf_cfg["batch_size"], shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=tf_cfg["batch_size"])
    test_loader = DataLoader(test_ds, batch_size=tf_cfg["batch_size"])

    # Model
    model = MultiLabelClassifier(
        model_name=tf_cfg["model_name"],
        num_labels=len(CRITIQUE_LABELS),
    ).to(device)

    # Class-weighted loss
    pos_weight = _compute_class_weights(y_train).to(device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight)

    # Optimizer + scheduler
    optimizer = torch.optim.AdamW(
        model.parameters(),
        lr=tf_cfg["learning_rate"],
        weight_decay=tf_cfg["weight_decay"],
    )

    total_steps = len(train_loader) * tf_cfg["num_epochs"]
    warmup_steps = int(total_steps * tf_cfg["warmup_ratio"])

    from transformers import get_linear_schedule_with_warmup

    scheduler = get_linear_schedule_with_warmup(
        optimizer, num_warmup_steps=warmup_steps, num_training_steps=total_steps
    )

    # Training loop
    best_val_loss = float("inf")
    patience_counter = 0
    out_dir = Path(model_dir or project_root() / "models" / "transformer")
    ensure_dir(out_dir)

    grad_accum = tf_cfg.get("gradient_accumulation_steps", 1)
    use_fp16 = tf_cfg.get("fp16", False) and device.type == "cuda"
    scaler = torch.amp.GradScaler("cuda") if use_fp16 else None

    for epoch in range(tf_cfg["num_epochs"]):
        model.train()
        train_loss = 0.0
        optimizer.zero_grad()

        for step, batch in enumerate(train_loader):
            batch = {k: v.to(device) for k, v in batch.items()}
            labels = batch.pop("labels")

            if use_fp16:
                with torch.amp.autocast("cuda"):
                    logits = model(**batch)
                    loss = criterion(logits, labels) / grad_accum
                scaler.scale(loss).backward()
            else:
                logits = model(**batch)
                loss = criterion(logits, labels) / grad_accum
                loss.backward()

            if (step + 1) % grad_accum == 0:
                if use_fp16:
                    scaler.step(optimizer)
                    scaler.update()
                else:
                    optimizer.step()
                scheduler.step()
                optimizer.zero_grad()

            train_loss += loss.item() * grad_accum

        avg_train_loss = train_loss / len(train_loader)

        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                batch = {k: v.to(device) for k, v in batch.items()}
                labels = batch.pop("labels")
                logits = model(**batch)
                loss = criterion(logits, labels)
                val_loss += loss.item()

        avg_val_loss = val_loss / len(val_loader)
        logger.info(
            "Epoch %d/%d: train_loss=%.4f, val_loss=%.4f",
            epoch + 1,
            tf_cfg["num_epochs"],
            avg_train_loss,
            avg_val_loss,
        )

        # Early stopping
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            patience_counter = 0
            torch.save(model.state_dict(), out_dir / "best_model.pt")
            tokenizer.save_pretrained(str(out_dir))
            logger.info("Saved best model (val_loss=%.4f)", best_val_loss)
        else:
            patience_counter += 1
            if patience_counter >= tf_cfg["early_stopping_patience"]:
                logger.info("Early stopping at epoch %d", epoch + 1)
                break

    # Load best model and evaluate
    model.load_state_dict(torch.load(out_dir / "best_model.pt", weights_only=True))
    model.eval()

    def _predict(loader: DataLoader) -> tuple[np.ndarray, np.ndarray]:
        all_logits = []
        all_labels = []
        with torch.no_grad():
            for batch in loader:
                batch = {k: v.to(device) for k, v in batch.items()}
                labels = batch.pop("labels")
                logits = model(**batch)
                all_logits.append(logits.cpu().numpy())
                all_labels.append(labels.cpu().numpy())
        logits_arr = np.concatenate(all_logits, axis=0)
        labels_arr = np.concatenate(all_labels, axis=0)
        probs = 1.0 / (1.0 + np.exp(-logits_arr))  # sigmoid
        return probs, labels_arr

    val_probs, y_val_arr = _predict(val_loader)
    test_probs, y_test_arr = _predict(test_loader)

    logger.info("Transformer training complete. Model saved to %s", out_dir)

    return {
        "model_type": "transformer",
        "model_dir": str(out_dir),
        "splits": {
            "train_idx": df_train.index.tolist(),
            "val_idx": df_val.index.tolist(),
            "test_idx": df_test.index.tolist(),
        },
        "predictions": {
            "y_val": y_val_arr,
            "y_test": y_test_arr,
            "y_val_proba": val_probs,
            "y_test_proba": test_probs,
        },
        "best_val_loss": best_val_loss,
    }


def load_transformer_model(
    model_dir: str | Path,
    device: str | None = None,
) -> tuple[MultiLabelClassifier, Any]:
    """Load a saved transformer model + tokenizer."""
    from transformers import AutoTokenizer

    model_dir = Path(model_dir)
    config = load_yaml(project_root() / "configs" / "model_config.yaml")
    tf_cfg = config["transformer"]

    dev = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))

    model = MultiLabelClassifier(
        model_name=tf_cfg["model_name"],
        num_labels=len(CRITIQUE_LABELS),
    )
    model.load_state_dict(
        torch.load(model_dir / "best_model.pt", map_location=dev, weights_only=True)
    )
    model.to(dev)
    model.eval()

    tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
    return model, tokenizer
