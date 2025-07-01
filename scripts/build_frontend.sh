#!/bin/bash
# Build the React frontend for production

echo "🔨 Building React frontend..."

# Navigate to frontend directory
cd frontend || exit 1

# Install dependencies
echo "📦 Installing dependencies..."
npm install

# Build for production
echo "🏗️  Building for production..."
npm run build

echo "✅ Frontend build complete!"
echo "   Output: static/dist/"