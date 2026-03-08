#!/usr/bin/env bash
set -e

echo ""
echo "  ===================================="
echo "   Dexscreener CLI - Quick Install"
echo "  ===================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "  [ERROR] Python 3 not found. Install Python 3.11+ first."
    exit 1
fi

# Create venv if missing
if [ ! -d ".venv" ]; then
    echo "  Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate and install
echo "  Installing dependencies..."
source .venv/bin/activate
pip install -e . --quiet

echo ""
echo "  ===================================="
echo "   Install complete!"
echo "  ===================================="
echo ""
echo "  Run without activating:"
echo "    ./.venv/bin/ds doctor"
echo "    ./.venv/bin/ds quickstart --shell bash --goal live"
echo ""
echo "  Or activate first if you want short commands:"
echo "    source .venv/bin/activate"
echo "    ds doctor"
echo "    ds quickstart --shell bash --goal live"
echo ""
echo "  MCP server:"
echo "    ./.venv/bin/dexscreener-mcp   - Start MCP server (stdio)"
echo ""
