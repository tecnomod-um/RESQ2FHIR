from __future__ import annotations

import argparse
import json
from pathlib import Path

from .resource_counts import summarize_resource_counts
from .semantic_preservation import evaluate_semantic_preservation


def evaluate_job(normalized_csv: Path, bundle_dir: Path) -> dict:
    bundle_paths = sorted(Path(bundle_dir).glob("*.json"))
    return {
        "resourceCounts": summarize_resource_counts(bundle_paths),
        "semanticPreservation": evaluate_semantic_preservation(
            Path(normalized_csv), Path(bundle_dir)
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate RESQ2FHIR transformation evaluation"
    )
    parser.add_argument("--csv", required=True, help="Normalized CSV used by the converter")
    parser.add_argument("--bundles", required=True, help="Directory containing generated Bundles")
    parser.add_argument("--out", help="Optional JSON output path")
    args = parser.parse_args()

    report = evaluate_job(Path(args.csv), Path(args.bundles))
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(payload, encoding="utf-8")
    else:
        print(payload)


if __name__ == "__main__":
    main()
