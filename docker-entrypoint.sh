#!/bin/bash
set -e

# Start the local memory node in the background
echo "Starting ReasonRDN Private Node on port 8765..."
rdn-node &
NODE_PID=$!

# Define cleanup function to terminate the node on exit
cleanup() {
    echo "Stopping ReasonRDN Private Node (PID $NODE_PID)..."
    kill "$NODE_PID" 2>/dev/null || true
}
trap cleanup EXIT SIGINT SIGTERM

# Start the dashboard in the foreground
echo "Starting ReasonRDN Dashboard on port 8501..."
# Run Streamlit and bind to 0.0.0.0 so it's accessible externally
streamlit run -m rdn.dash --server.port=8501 --server.address=0.0.0.0
