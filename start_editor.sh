#!/bin/bash

# Start the Karaoke Maker Web Editor
cd "$(dirname "$0")"

echo ""
echo "======================================================================"
echo "  KARAOKE MAKER - WEB EDITOR"
echo "======================================================================"
echo ""
echo "Starting web server..."
echo ""
echo "Open your browser to: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop the server"
echo "======================================================================"
echo ""

python3 web_editor.py
