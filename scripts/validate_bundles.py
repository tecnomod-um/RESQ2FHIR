import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import httpx


DEFAULT_VALIDATOR_BASE_URL = os.getenv("VALIDATOR_BASE_URL", "http://localhost:8085")
DEFAULT_VALIDATOR_PATH = os.getenv("VALIDATOR_PATH", "/api/validate/bundle")


def _validator_url() -> str:
    base = DEFAULT_VALIDATOR_BASE_URL.rstrip("/") + "/"
    path = DEFAULT_VALIDATOR_PATH.lstrip("/")
    return urljoin(base, path)


def _count_issues(outcome: dict[str, Any]) -> dict[str, int]:
    counts = {"fatal": 0, "error": 0, "warning": 0, "information": 0}
    for issue in outcome.get("issue") or []:
        severity = str(issue.get("severity") or "").lower()
        if severity in counts:
            counts[severity] += 1
    return counts


def _without_information_issues(outcome: dict[str, Any]) -> dict[str, Any]:
    filtered = dict(outcome)
    filtered["issue"] = [
        issue for issue in outcome.get("issue") or []
        if str(issue.get("severity") or "").lower() != "information"
    ]
    filtered.pop("text", None)
    return filtered


def _failure_outcome(message: str) -> dict[str, Any]:
    return {
        "resourceType": "OperationOutcome",
        "issue": [
            {
                "severity": "fatal",
                "code": "exception",
                "diagnostics": message,
            }
        ],
    }


def _validate_one(
    bundle_path: Path,
    outcomes_dir: Path,
    validator_url: str,
    profile: str | None,
    timeout_seconds: float,
) -> dict[str, Any]:
    params = {"profile": profile} if profile else None
    outcome_path = outcomes_dir / f"{bundle_path.stem}.oo.json"
    started = time.time()

    try:
        with httpx.Client(timeout=httpx.Timeout(timeout_seconds, connect=10.0)) as client:
            response = client.post(
                validator_url,
                params=params,
                content=bundle_path.read_bytes(),
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            outcome = response.json()
    except Exception as exc:
        outcome = _failure_outcome(f"Validator call failed for {bundle_path.name}: {exc}")

    outcome = _without_information_issues(outcome)
    outcome_path.write_text(json.dumps(outcome, ensure_ascii=False, indent=2), encoding="utf-8")
    issues = _count_issues(outcome)

    return {
        "bundle": bundle_path.name,
        "outcome": str(outcome_path),
        "issues": issues,
        "durationMs": int((time.time() - started) * 1000),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate generated FHIR Bundle JSON files and persist OperationOutcome files."
    )
    parser.add_argument("--bundles-dir", required=True, help="Directory containing generated Bundle *.json files.")
    parser.add_argument(
        "--outcomes-dir",
        help="Directory where *.oo.json OperationOutcome files will be written. Defaults to <bundles-dir>/../outcomes.",
    )
    parser.add_argument("--validator-url", default=_validator_url(), help="FHIR validator bundle endpoint URL.")
    parser.add_argument("--profile", default=None, help="Optional canonical profile URL passed to the validator.")
    parser.add_argument("--parallelism", type=int, default=4, help="Number of concurrent validation requests.")
    parser.add_argument("--limit", type=int, default=None, help="Validate only the first N bundles.")
    parser.add_argument("--timeout", type=float, default=120.0, help="Per-bundle validator timeout in seconds.")
    parser.add_argument(
        "--summary",
        help="Summary JSON path. Defaults to <outcomes-dir>/validation-summary.json.",
    )
    parser.add_argument(
        "--no-fail-on-error",
        action="store_true",
        help="Exit with code 0 even when the OperationOutcome contains fatal/error issues.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    bundles_dir = Path(args.bundles_dir).resolve()
    outcomes_dir = Path(args.outcomes_dir).resolve() if args.outcomes_dir else (bundles_dir.parent / "outcomes")
    summary_path = Path(args.summary).resolve() if args.summary else (outcomes_dir / "validation-summary.json")

    if not bundles_dir.exists():
        print(f"Bundles directory does not exist: {bundles_dir}", file=sys.stderr)
        return 2

    paths = sorted(p for p in bundles_dir.glob("*.json") if not p.name.endswith(".oo.json"))
    if args.limit is not None:
        paths = paths[: args.limit]
    if not paths:
        print(f"No Bundle JSON files found in {bundles_dir}", file=sys.stderr)
        return 2

    outcomes_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()
    totals = {"fatal": 0, "error": 0, "warning": 0, "information": 0}
    rows: list[dict[str, Any]] = []

    workers = max(1, int(args.parallelism))
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(
                _validate_one,
                path,
                outcomes_dir,
                args.validator_url,
                args.profile,
                args.timeout,
            )
            for path in paths
        ]
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            for severity, value in row["issues"].items():
                totals[severity] += value
            print(
                f"{row['bundle']}: fatal={row['issues']['fatal']} "
                f"error={row['issues']['error']} warning={row['issues']['warning']} "
                f"information={row['issues']['information']}"
            )

    rows.sort(key=lambda row: row["bundle"])
    summary = {
        "validatorUrl": args.validator_url,
        "profile": args.profile,
        "bundlesDir": str(bundles_dir),
        "outcomesDir": str(outcomes_dir),
        "startedAt": datetime.fromtimestamp(started, UTC).isoformat().replace("+00:00", "Z"),
        "finishedAt": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "durationMs": int((time.time() - started) * 1000),
        "totalBundles": len(paths),
        "bySeverity": totals,
        "totals": {
            "errors": totals["fatal"] + totals["error"],
            "warnings": totals["warning"],
            "information": totals["information"],
        },
        "bundles": rows,
    }
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Validation summary written to {summary_path}")
    print(
        f"Validated {len(paths)} bundles: errors={summary['totals']['errors']} "
        f"warnings={summary['totals']['warnings']} information={summary['totals']['information']}"
    )

    if summary["totals"]["errors"] and not args.no_fail_on_error:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
