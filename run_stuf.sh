#!/usr/bin/env bash

# Exit immediately if any command fails
set -e

echo "--- Running Simple Build and Execute ---"

# 1. Navigate to the scripts directory
echo "[1/5] Changing directory to 'scripts'..."
cd scripts

# 2. Run the Python script
echo "[2/5] Running Python script 'fromJSONtoPL.py'..."
python3 fromJSONtoPL.py

# 3. Navigate to the src directory (relative to 'scripts')
echo "[3/5] Changing directory to '../src'..."
cd ../src

# 4. Run make
echo "[4/5] Running 'make'..."
make

# 5. Run the executable
echo "[5/5] Running './recommend'..."
./recommend

echo "--- Script finished successfully ---"