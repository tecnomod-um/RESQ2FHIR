#!/usr/bin/env python3
"""
Basic integration test for RESQ2FHIR converter.

Validates that:
1. Data can be loaded from CSV
2. Converter generates valid FHIR bundles
3. Output JSON is well-formed

Usage:
    python test_converter.py
    python test_converter.py --verbose
"""

import argparse
import json
import sys
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def setup_logging(verbose=False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )


def test_csv_load():
    """Test that CSV can be loaded."""
    logger.info("Test 1: Loading CSV...")
    try:
        import pandas as pd
        csv_file = Path("data/data-extended.csv")
        if not csv_file.exists():
            logger.warning(f"CSV not found: {csv_file}")
            return False
        
        df = pd.read_csv(csv_file)
        logger.info(f"✓ Loaded {len(df)} rows, {len(df.columns)} columns")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to load CSV: {e}")
        return False


def test_converter_imports():
    """Test that all required modules can be imported."""
    logger.info("Test 2: Checking module imports...")
    try:
        from scripts import transform
        from scripts import data_modeling
        from scripts import utils
        logger.info("✓ All modules imported successfully")
        return True
    except ImportError as e:
        logger.error(f"✗ Import failed: {e}")
        return False


def test_converter_execution():
    """Test converter on a small sample."""
    logger.info("Test 3: Running converter on sample...")
    try:
        import tempfile
        from pathlib import Path
        import pandas as pd
        from scripts.transform import process_csv
        
        csv_file = Path("data/data-extended.csv")
        if not csv_file.exists():
            logger.warning("Input CSV not found, skipping")
            return False
        
        # Create temp dir for output
        with tempfile.TemporaryDirectory() as tmpdir:
            # Load first 5 rows as test data
            df = pd.read_csv(csv_file)
            test_csv = Path(tmpdir) / "test.csv"
            df.head(5).to_csv(test_csv, index=False)
            
            # Run converter
            output_dir = Path(tmpdir) / "output"
            exit_code = process_csv(
                csv_path=str(test_csv),
                output_dir=str(output_dir),
                verbose=False
            )
            
            if exit_code != 0:
                logger.error(f"✗ Converter exited with code {exit_code}")
                return False
            
            # Check output
            bundles = list(output_dir.glob("*.json"))
            if not bundles:
                logger.error("✗ No bundles generated")
                return False
            
            logger.info(f"✓ Generated {len(bundles)} bundles")
            
            # Validate first bundle
            try:
                with open(bundles[0], 'r') as f:
                    bundle = json.load(f)
                
                assert bundle.get("resourceType") == "Bundle"
                assert bundle.get("type") == "transaction"
                assert "entry" in bundle
                assert len(bundle["entry"]) > 0
                
                logger.info(f"✓ Bundle structure valid ({len(bundle['entry'])} entries)")
                return True
            except Exception as e:
                logger.error(f"✗ Bundle validation failed: {e}")
                return False
                
    except Exception as e:
        logger.error(f"✗ Converter test failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="RESQ2FHIR converter tests")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    
    print("\n" + "=" * 60)
    print("RESQ2FHIR - Converter Integration Tests")
    print("=" * 60 + "\n")
    
    results = {
        "CSV Load": test_csv_load(),
        "Module Imports": test_converter_imports(),
        "Converter Execution": test_converter_execution(),
    }
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("-" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print("-" * 60)
    print(f"Total: {passed}/{total} passed")
    print("=" * 60 + "\n")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
