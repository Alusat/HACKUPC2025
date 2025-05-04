#!/usr/bin/env bash

# Exit immediately if any command fails
set -e

echo "--- Running Simple Build and Execute ---"

[ -f "data/user_info.json" ] && rm "data/user_info.json"
[ -f "data/final_scored.json" ] && rm "data/final_scored.json"

echo "calling server"
node server/server.js &

echo "Running 'npx live-server for index..."
npx live-server --open=index.html &

while [ ! -f "data/user_info.json" ]; do
    echo "File not found. Waiting..."
    sleep 0.50  # Wait for 1 second before checking again
done

sleep 1.5

# 1. Navigate to the scripts directory
echo "[1/6] Changing directory to 'scripts'..."
cd scripts

# 2. Run the Python script
echo "[2/6] Running Python script 'fromJSONtoPL.py'..."
python3 fromJSONtoPL.py

# 3. Navigate to the src directory (relative to 'scripts')
echo "[3/6] Changing directory to '../src'..."
cd ../src

# 4. Run make
echo "[4/6] Running 'make'..."
make

# 5. Run the executable
echo "[5/6] Running './recommend'..."

./recommend

cd ../scripts

sleep 1

echo "ejecutando codigo de pito"
python3 fetch_flights.py

cd ..

while [ ! -f "data/final_scored.json" ]; do
    echo "Final scored not found. Waiting..."
    sleep 0.50  # Wait for 1 second before checking again
done

# 6. 
echo "[6/6] Running 'npx live-server..."
npx live-server --open=output.html &

sleep 1

echo "--- Script finished successfully ---"