#!/bin/bash

set -e

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SOURCE="$ROOT/custom_components/wfd"
TARGET="/Volumes/config/custom_components/wfd"

echo ""
echo "🍽️  What's For Dinner? Deployment"
echo "================================="

if [ ! -d "/Volumes/config" ]; then
    echo "❌ Home Assistant config share is not mounted."
    exit 1
fi

mkdir -p /Volumes/config/custom_components

echo "🗑️  Removing previous version..."
rm -rf "$TARGET"

echo "📦 Copying integration..."
cp -R "$SOURCE" "$TARGET"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Restart Home Assistant to load the changes."