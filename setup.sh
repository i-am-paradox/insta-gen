#!/bin/bash

set -e

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║       Instagram Creator PRO — Setup Script           ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# ── Check Python ──
if ! command -v python3 &>/dev/null; then
    echo "❌ Python3 not found. Install from https://python.org"
    exit 1
fi

PYTHON_VER=$(python3 -c "import sys; print(sys.version_info.minor)")
if [ "$PYTHON_VER" -lt 10 ]; then
    echo "❌ Python 3.10+ required. Current: $(python3 --version)"
    exit 1
fi
echo "✅ Python: $(python3 --version)"

# ── Check Node.js ──
if ! command -v node &>/dev/null; then
    echo "❌ Node.js not found. Install from https://nodejs.org"
    exit 1
fi
echo "✅ Node.js: $(node --version)"

# ── Install Python dependencies ──
echo ""
echo "📦 Installing Python dependencies..."
pip3 install --break-system-packages -r requirements_pro.txt -q
echo "✅ Python packages installed"

# ── Download Camoufox browser ──
echo ""
echo "🦊 Downloading Camoufox stealth browser..."
python3 -m camoufox fetch
echo "✅ Camoufox ready"

# ── Install frontend dependencies ──
echo ""
echo "🎨 Installing frontend dependencies..."
cd frontend && npm install --silent && cd ..
echo "✅ Frontend packages installed"

# ── Copy .env if not exists ──
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✅ .env created from template"
else
    echo "✅ .env already exists"
fi

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║   ✅ Setup Complete! Now run:                        ║"
echo "║                                                      ║"
echo "║       bash start.sh                                  ║"
echo "║                                                      ║"
echo "║   Then open: http://localhost:5173                   ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""
