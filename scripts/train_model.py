from __future__ import annotations

import argparse
import csv
from pathlib import Path


LABELS = {"low": 0, "medium": 1, "high": 2}


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a PyTorch risk classifier artifact.")
    parser.add_argument("--data", required=True, help="CSV dataset path")
    parser.add_argument("--output", default="models/risk_classifier.pt", help="Output torchscript path")
    parser.add_argument("--epochs", type=int, default=200)
    args = parser.parse_args()

    try:
        import torch
        from torch import nn
    except ImportError as exc:
        raise SystemExit("Install the ai extra to train models: pip install -e '.[ai]'") from exc

    features, labels = load_dataset(Path(args.data))
    x = torch.tensor(features, dtype=torch.float32)
    y = torch.tensor(labels, dtype=torch.long)

    model = nn.Sequential(nn.Linear(5, 16), nn.ReLU(), nn.Linear(16, 3))
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    loss_fn = nn.CrossEntropyLoss()

    for _ in range(args.epochs):
        optimizer.zero_grad()
        loss = loss_fn(model(x), y)
        loss.backward()
        optimizer.step()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    scripted = torch.jit.script(model)
    scripted.save(str(output))
    print(f"Saved model artifact to {output}")


def load_dataset(path: Path) -> tuple[list[list[float]], list[int]]:
    rows: list[list[float]] = []
    labels: list[int] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            prior_claims = min(float(row.get("prior_claims", 0)) / 5, 1.0)
            claim_severity = min(float(row.get("claim_severity", 0)) / 100_000, 1.0)
            coverage_amount = min(float(row.get("coverage_amount", 0)) / 1_000_000, 1.0)
            geographic_risk = min(float(row.get("geographic_risk", 0)), 1.0)
            missing_fields = min(float(row.get("missing_fields", 0)) / 7, 1.0)
            label = row.get("risk_label", "").strip().lower()
            if label not in LABELS:
                raise ValueError(f"Unsupported risk_label: {label}")
            rows.append([prior_claims, coverage_amount, missing_fields, geographic_risk, claim_severity])
            labels.append(LABELS[label])
    if not rows:
        raise ValueError("Dataset is empty")
    return rows, labels


if __name__ == "__main__":
    main()

