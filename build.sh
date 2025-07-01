#!/bin/bash
set -e

echo "=== Starting Frontend Build ==="
echo "Current directory: $(pwd)"
echo "Directory contents:"
ls -la

if [ -d "frontend" ]; then
    echo "Frontend directory found"
    cd frontend
    echo "Frontend contents:"
    ls -la
    
    echo "Installing dependencies..."
    npm install
    
    echo "Building React app..."
    npm run build
    
    cd ..
    echo "Build complete. Checking output..."
    ls -la static/dist/ || echo "No dist directory found"
else
    echo "ERROR: frontend directory not found!"
    exit 1
fi