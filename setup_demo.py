#!/usr/bin/env python3
"""
Setup and quick-start script for RESQ2FHIR.

Usage:
    python setup_demo.py
"""

import subprocess
import sys
from pathlib import Path


def print_header(msg):
    print("\n" + "=" * 60)
    print(msg)
    print("=" * 60 + "\n")


def print_step(num, msg):
    print(f"\n[Step {num}] {msg}")
    print("-" * 60)


def run_cmd(cmd, shell=False):
    """Run a command and return exit code."""
    print(f"Running: {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
    result = subprocess.run(cmd, shell=shell, capture_output=False)
    return result.returncode


def main():
    print_header("RESQ2FHIR - Quick Start Setup")
    
    project_root = Path(__file__).parent.resolve()
    print(f"Project root: {project_root}")
    
    # Step 1: Check Python version
    print_step(1, "Checking Python version")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"❌ Python 3.9+ required, found {version.major}.{version.minor}")
        sys.exit(1)
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    
    # Step 2: Check dependencies
    print_step(2, "Installing dependencies")
    req_file = project_root / "requirements.txt"
    if req_file.exists():
        exit_code = run_cmd([sys.executable, "-m", "pip", "install", "-r", str(req_file)])
        if exit_code != 0:
            print("❌ Failed to install dependencies")
            sys.exit(1)
        print("✓ Dependencies installed")
    else:
        print("⚠ requirements.txt not found")
    
    # Step 3: Check input data
    print_step(3, "Checking input data")
    csv_file = project_root / "data" / "data-extended.csv"
    if csv_file.exists():
        print(f"✓ Input CSV found: {csv_file.name}")
    else:
        print(f"⚠ Input CSV not found: {csv_file}")
    
    # Step 4: Test converter
    print_step(4, "Testing converter (first 10 rows)")
    output_dir = project_root / "demo_output"
    output_dir.mkdir(exist_ok=True)
    
    # Create a small test CSV with just first 10 rows
    if csv_file.exists():
        try:
            import pandas as pd
            df = pd.read_csv(csv_file)
            test_csv = project_root / "demo_test.csv"
            df.head(10).to_csv(test_csv, index=False)
            print(f"✓ Created test CSV with 10 rows: {test_csv.name}")
            
            # Run converter
            cmd = [
                sys.executable,
                "scripts/transform.py",
                "--input", str(test_csv),
                "--outdir", str(output_dir)
            ]
            exit_code = run_cmd(cmd)
            
            if exit_code == 0:
                bundles = list(output_dir.glob("*.json"))
                print(f"✓ Converter produced {len(bundles)} bundles")
                for bundle_file in bundles[:3]:
                    print(f"  - {bundle_file.name}")
                if len(bundles) > 3:
                    print(f"  ... and {len(bundles) - 3} more")
            else:
                print("⚠ Converter test failed (see above for details)")
            
            # Cleanup
            test_csv.unlink()
            
        except Exception as e:
            print(f"⚠ Could not run test: {e}")
    
    # Step 5: Show next steps
    print_header("Setup Complete!")
    print("""
Next Steps:

1. Run the converter on your full data:
   python scripts/transform.py --input data/data-extended.csv --outdir ./bundles --verbose

2. Start the FastAPI server:
   uvicorn scripts.main:app --reload

3. Upload CSV via API:
   curl -X POST http://localhost:8000/jobs/csv \\
     -F "file=@data/data-extended.csv"

4. Check the README for detailed usage and configuration:
   README.md

Configuration:
   Copy .env.example to .env and customize as needed.
   Key variable: CONVERTER_CMD
    """)


if __name__ == "__main__":
    main()
