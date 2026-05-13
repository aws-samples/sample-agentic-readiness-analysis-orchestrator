#!/bin/bash

echo "🏗️  Building and deploying monolithic e-commerce application..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Build and start the container
echo "📦 Building Docker image..."
docker-compose build

echo ""
echo "🚀 Starting application..."
docker-compose up -d

echo ""
echo "⏳ Waiting for application to be ready..."
sleep 5

# Check if the application is healthy
if curl -f http://localhost:8080/api/products > /dev/null 2>&1; then
    echo ""
    echo "✅ Monolith is running successfully!"
    echo ""
    echo "🌐 Access the application at: http://localhost:8080"
    echo ""
    echo "📊 View logs with: docker-compose logs -f"
    echo "🛑 Stop with: docker-compose down"
else
    echo ""
    echo "⚠️  Application started but health check failed."
    echo "Check logs with: docker-compose logs"
fi
