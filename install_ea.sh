#!/bin/bash

echo "🚀 Installing Gold Digger Expert Advisor to MT5"
echo "================================================"

# Define paths
GOLD_DIGGER_PATH="/Users/vladinnikolov/Downloads/Gold Digger"
MT5_EXPERTS_PATH="/Users/vladinnikolov/Library/Application Support/net.metaquotes.wine.metatrader5/drive_c/Program Files/MetaTrader 5/MQL5/Experts"
EA_SOURCE="$GOLD_DIGGER_PATH/mql5/GoldDiggerEA.mq5"
EA_DEST="$MT5_EXPERTS_PATH/GoldDigger"

echo "📁 Source EA: $EA_SOURCE"
echo "📁 Destination: $EA_DEST"

# Check if source file exists
if [ ! -f "$EA_SOURCE" ]; then
    echo "❌ Error: GoldDiggerEA.mq5 not found at $EA_SOURCE"
    exit 1
fi

# Create destination directory
echo "📂 Creating Experts directory..."
mkdir -p "$EA_DEST"

if [ $? -eq 0 ]; then
    echo "✅ Directory created successfully"
else
    echo "❌ Failed to create directory"
    exit 1
fi

# Copy EA file
echo "📋 Copying Expert Advisor..."
cp "$EA_SOURCE" "$EA_DEST/"

if [ $? -eq 0 ]; then
    echo "✅ Expert Advisor copied successfully"
else
    echo "❌ Failed to copy Expert Advisor"
    exit 1
fi

# Verify installation
if [ -f "$EA_DEST/GoldDiggerEA.mq5" ]; then
    echo "✅ Installation verified"
    echo ""
    echo "📋 NEXT STEPS:"
    echo "1. Open MetaTrader 5"
    echo "2. Press F4 to open MetaEditor"
    echo "3. Navigate to Experts/GoldDigger/GoldDiggerEA.mq5"
    echo "4. Press F7 to compile"
    echo "5. Drag EA to XAUUSD chart"
    echo "6. Enable AutoTrading (Ctrl+E)"
    echo ""
    echo "🎯 EA will communicate with Python via:"
    echo "   📊 Signals: /Users/Shared/GoldDigger/gold_digger_signals.json"
    echo "   📈 Results: /Users/Shared/GoldDigger/gold_digger_results.json"
    echo ""
    echo "🚀 Ready for automated trading!"
else
    echo "❌ Installation verification failed"
    exit 1
fi
