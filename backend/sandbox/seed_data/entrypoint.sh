#!/bin/bash
# Start fake internal API in background
python3 /opt/internal-api/server.py &

# Keep container alive waiting for commands
tail -f /dev/null
