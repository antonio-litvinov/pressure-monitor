#!/usr/bin/env bash
set -e

export PYTHONUNBUFFERED=1

# Set default values if variables are unset or empty:
export GIGADOC_ADAPTER_IP=${GIGADOC_ADAPTER_IP:-"0.0.0.0"}
export GIGADOC_ADAPTER_PORT=${GIGADOC_ADAPTER_PORT:-"5000"}
export GIGADOC_ADAPTER_DIR=${GIGADOC_ADAPTER_DIR:-"/tmp/gigadoc_cache/"}
export GIGADOC_WS_SERVER_IP=${GIGADOC_WS_SERVER_IP:-"127.0.0.1"}
export GIGADOC_WS_SERVER_PORT=${GIGADOC_WS_SERVER_PORT:-"9000"}
# Start gunicorn server
gunicorn -w 4 -b $GIGADOC_ADAPTER_IP:$GIGADOC_ADAPTER_PORT adapter_interface:app &
gunicorn_pid=$!
echo "Adapter interface started with PID: $gunicorn_pid"
# Start the Python processor script
python3 adapter_processor.py &
processor_pid=$!
echo "Adapter processor started with PID: $processor_pid"
# Set trap to kill processes on SIGINT
trap "kill $gunicorn_pid $processor_pid; exit" SIGINT
echo "Trap set for SIGINT to kill adapter processes, waiting..."
# Wait for both processes to finish
wait

echo "something after 'wait' command"

