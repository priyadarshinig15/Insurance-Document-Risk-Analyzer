from __future__ import annotations

import argparse
from pathlib import Path

from scripts.train_model import load_dataset


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a trained PyTorch risk classifier.")
    parser.add_argument("--data", required=True)
    parser.add_argument("--model", default="models/risk_classifier.pt")
    args = parser.parse_args()

    try:
        import torch
    except ImportError as exc:
        raise SystemExit("Install the ai extra to validate models: pip install -e '.[ai]'") from exc

    features, labels = load_dataset(Path(args.data))
    model = torch.jit.load(args.model)
    model.eval()
    x = torch.tensor(features, dtype=torch.float32)
    y = torch.tensor(labels, dtype=torch.long)
    with torch.no_grad():
        predictions = model(x).argmax(dim=1)
    accuracy = (predictions == y).float().mean().item()
    print(f"accuracy={accuracy:.3f}")
    if accuracy < 0.60:
        raise SystemExit("Model accuracy is below the minimum validation threshold")


if __name__ == "__main__":
    main()

