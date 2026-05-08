"""
Main converter: CSV → FHIR Bundles.

This script reads a CSV file containing stroke patient data and transforms
each row into a complete FHIR Bundle containing Patient, Encounter, Conditions,
Observations, Procedures, and Medications.

Usage:
    python transform.py --input data.csv --outdir /path/to/output

The script generates one JSON file per patient (case) in the output directory.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd
from fhir.resources.bundle import Bundle 
import uuid
from decimal import Decimal
import numpy as np
import datetime as dt

# Import FHIR builders
from data_modeling import transform_to_fhir
from utils import TransformError 


logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )


def load_csv(csv_path: Path) -> pd.DataFrame:
    """Load CSV file and return DataFrame."""
    logger.info(f"Loading CSV from {csv_path}")
    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
        logger.info(f"Loaded {len(df)} rows from CSV")
        return df
    except Exception as e:
        raise TransformError(f"Failed to load CSV '{csv_path}': {e}")


def row_to_dict(row: pd.Series) -> Dict[str, Any]:
    """Convert pandas Series row to dict, handling NaN values."""
    result = {}
    for key, value in row.items():
        # Skip NaN/None values
        if pd.isna(value):
            result[key] = None
        else:
            # Keep string representation if it's a string
            if isinstance(value, str):
                result[key] = value.strip() if value.strip() else None
            else:
                result[key] = value
    return result


def transform_row_to_bundle(row: pd.Series, row_idx: int) -> Optional[Bundle]:
    """
    Transform a single CSV row into a FHIR Bundle.
    
    Returns:
        Bundle if successful, None if row should be skipped.
    """
    try:
        raw_dict = row_to_dict(row)
        file_id = str(raw_dict.get("case", f"case_{row_idx}"))
        
        if not file_id or file_id == "None":
            logger.warning(f"Row {row_idx}: Missing case, skipping")
            return None
        
        logger.debug(f"Transforming row {row_idx}: case={file_id}")
        
        # Call the main transformation orchestrator
        bundle = transform_to_fhir(file_id, raw_dict)
        return bundle
        
    except TransformError as e:
        logger.error(f"Row {row_idx}: Transformation error: {e}")
        return None
    except Exception as e:
        logger.error(f"Row {row_idx}: Unexpected error: {e}", exc_info=True)
        return None


def bundle_to_json_dict(bundle: Bundle) -> Dict[str, Any]:
    """
    Convert a Bundle resource to a JSON-serializable dictionary.
    Uses the fhir.resources built-in serialization.
    """
    def bundle_to_dict(bundle_obj) -> dict:
        """
        Supports serialization from different bundle object types:
        - pydantic v2 (`model_dump`)
        - pydantic v1 (`dict`)
        - objects with `.json()`
        - already-dict or JSON string
        """
        if bundle_obj is None:
            raise ValueError("transform_to_fhir did not return a valid Bundle (None)")
        # pydantic v2
        if hasattr(bundle_obj, "model_dump"):
            return bundle_obj.model_dump(by_alias=True)
        # pydantic v1
        if hasattr(bundle_obj, "dict"):
            try:
                return bundle_obj.dict(by_alias=True)
            except TypeError:
                return bundle_obj.dict()
        # has .json()
        if hasattr(bundle_obj, "json"):
            return json.loads(bundle_obj.json())
        # already a dict
        if isinstance(bundle_obj, dict):
            return bundle_obj
        # is JSON string
        if isinstance(bundle_obj, str):
            return json.loads(bundle_obj)
        raise TypeError(f"Cannot serialize the type returned by transform_to_fhir: {type(bundle_obj)}")

    def ensure_fullurls(bundle_dict: dict, absolute_base: str | None = None) -> dict:
        """
        Ensures each entry has a valid `fullUrl` and that resource `id`s exist.
        - If `absolute_base` provided, uses `{absolute_base}/{ResourceType}/{id}`
        - Otherwise generates `urn:uuid:<hex>` (lowercase)
        Also normalizes urn:uuid to lowercase.
        """
        entries = bundle_dict.get("entry") or []
        for i, e in enumerate(entries):
            if not isinstance(e, dict):
                # try to coerce
                try:
                    e = dict(e)
                except Exception:
                    continue
            res = (e.get("resource") or {})
            rtype = res.get("resourceType")
            rid = res.get("id")
            fu = e.get("fullUrl")

            # ensure id
            if not rid:
                rid = uuid.uuid4().hex
                res["id"] = rid

            ok = False
            if isinstance(fu, str):
                if fu.startswith("urn:uuid:"):
                    try:
                        u = fu.split("urn:uuid:", 1)[1]
                        e["fullUrl"] = f"urn:uuid:{u.lower()}"
                        ok = True
                    except Exception:
                        pass
                elif fu.startswith("http://") or fu.startswith("https://"):
                    ok = True

            if not ok:
                if absolute_base and rtype and rid:
                    e["fullUrl"] = f"{absolute_base.rstrip('/')}/{rtype}/{rid}"
                else:
                    e["fullUrl"] = f"urn:uuid:{uuid.uuid4().hex}"

            e["resource"] = res
            entries[i] = e
        bundle_dict["entry"] = entries
        return bundle_dict

    def remove_nulls(obj):
        """Recursively remove keys with value None from dicts and filter None from lists."""
        if isinstance(obj, dict):
            new = {}
            for k, v in obj.items():
                if v is None:
                    continue
                nv = remove_nulls(v)
                # skip empty containers
                if nv is None:
                    continue
                new[k] = nv
            return new
        elif isinstance(obj, list):
            new_list = []
            for item in obj:
                if item is None:
                    continue
                ri = remove_nulls(item)
                if ri is None:
                    continue
                new_list.append(ri)
            return new_list
        else:
            return obj

    try:
        bdict = bundle_to_dict(bundle)
        # ensure fullUrls (no absolute base by default)
        bdict = ensure_fullurls(bdict, absolute_base=None)
        # remove None fields recursively
        bdict = remove_nulls(bdict)
        # ensure minimal structure
        if "resourceType" not in bdict:
            bdict["resourceType"] = "Bundle"
        if "type" not in bdict or not bdict.get("type"):
            bdict["type"] = "transaction"
        if "entry" not in bdict:
            bdict["entry"] = []
        return bdict
    except Exception as e:
        logger.warning(f"Failed to serialize bundle: {e}")
        # Fallback: use json.loads/dumps
        try:
            return json.loads(bundle.json())
        except Exception:
            raise


def process_csv(csv_path: Path, output_dir: Path, verbose: bool = False):
    """
    Main processing function: read CSV, transform to FHIR Bundles, write JSON files.
    """
    setup_logging(verbose)
    
    logger.info("=" * 60)
    logger.info("RESQ2FHIR Converter - CSV to FHIR Bundles")
    logger.info("=" * 60)
    
    # Validate input
    csv_path = Path(csv_path).resolve()
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    # Prepare output directory
    output_dir = Path(output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Output directory: {output_dir}")
    
    # Load CSV
    df = load_csv(csv_path)
    
    # Statistics
    total_rows = len(df)
    successful = 0
    failed = 0
    skipped = 0
    
    logger.info(f"Starting transformation of {total_rows} rows...")
    
    # Process each row
    for idx, (_, row) in enumerate(df.iterrows(), start=1):
        logger.debug(f"Processing row {idx}/{total_rows}")
        
        bundle = transform_row_to_bundle(row, idx)
        
        if bundle is None:
            skipped += 1
            continue
        
        try:
            # Get case for filename
            case = row.get("case", f"case_{idx}")
            output_file = output_dir / f"{case}.json"
            
            # Serialize bundle
            bundle_dict = bundle_to_json_dict(bundle)

            def make_json_safe(obj):
                """Recursively convert Decimal and numpy types to native Python types."""
                if isinstance(obj, Decimal):
                    return float(obj)
                # datetimes -> ISO strings
                if isinstance(obj, (dt.datetime, dt.date, dt.time)):
                    try:
                        return obj.isoformat()
                    except Exception:
                        return str(obj)
                # numpy scalars
                if isinstance(obj, (np.integer,)):
                    return int(obj)
                if isinstance(obj, (np.floating,)):
                    return float(obj)
                if isinstance(obj, (np.bool_,)):
                    return bool(obj)
                if isinstance(obj, dict):
                    return {k: make_json_safe(v) for k, v in obj.items()}
                if isinstance(obj, list):
                    return [make_json_safe(v) for v in obj]
                return obj

            bundle_safe = make_json_safe(bundle_dict)

            # Write JSON file
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(bundle_safe, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✓ {idx}/{total_rows}: {case} → {output_file.name}")
            successful += 1
            
        except Exception as e:
            logger.error(f"Row {idx}: Failed to write bundle: {e}")
            failed += 1
    
    # Summary
    logger.info("=" * 60)
    logger.info("Conversion Summary:")
    logger.info(f"  Total rows:    {total_rows}")
    logger.info(f"  Successful:    {successful}")
    logger.info(f"  Failed:        {failed}")
    logger.info(f"  Skipped:       {skipped}")
    logger.info(f"  Output files:  {len(list(output_dir.glob('*.json')))}")
    logger.info("=" * 60)
    
    # Exit with appropriate code
    if failed > 0:
        logger.error("Some rows failed transformation. Review logs above.")
        return 1
    
    if successful == 0:
        logger.error("No bundles were generated.")
        return 1
    
    logger.info("Conversion completed successfully!")
    return 0


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Transform RESQ CSV data to FHIR Bundles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python transform.py --input data/data-extended.csv --outdir ./bundles
  python transform.py --input data.csv --outdir /tmp/out --verbose
        """
    )
    
    parser.add_argument(
        "--input", "-i",
        required=True,
        help="Path to input CSV file"
    )
    
    parser.add_argument(
        "--outdir", "-o",
        required=True,
        help="Path to output directory (will be created if needed)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose (DEBUG) logging"
    )
    
    args = parser.parse_args()
    
    try:
        exit_code = process_csv(
            csv_path=args.input,
            output_dir=args.outdir,
            verbose=args.verbose
        )
        sys.exit(exit_code)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
