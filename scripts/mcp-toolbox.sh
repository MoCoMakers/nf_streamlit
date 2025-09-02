#!/bin/bash

# MCP Toolbox Management Script
# This script helps manage the MCP Toolbox Docker container

CONTAINER_NAME="mcp-toolbox"
IMAGE="us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest"
TOOLS_FILE="./tools.yaml"

case "$1" in
    start)
        echo "Starting MCP Toolbox container..."
        docker run -d --name $CONTAINER_NAME -p 5000:5000 -v $TOOLS_FILE:/app/tools.yaml $IMAGE --tools-file /app/tools.yaml
        echo "MCP Toolbox container started with name: $CONTAINER_NAME"
        ;;
    stop)
        echo "Stopping MCP Toolbox container..."
        docker stop $CONTAINER_NAME
        echo "MCP Toolbox container stopped"
        ;;
    restart)
        echo "Restarting MCP Toolbox container..."
        docker stop $CONTAINER_NAME 2>/dev/null
        docker rm $CONTAINER_NAME 2>/dev/null
        docker run -d --name $CONTAINER_NAME -p 5000:5000 -v $TOOLS_FILE:/app/tools.yaml $IMAGE --tools-file /app/tools.yaml
        echo "MCP Toolbox container restarted"
        ;;
    status)
        echo "MCP Toolbox container status:"
        docker ps | grep $CONTAINER_NAME
        ;;
    logs)
        echo "MCP Toolbox container logs:"
        docker logs $CONTAINER_NAME
        ;;
    clean)
        echo "Cleaning up MCP Toolbox container..."
        docker stop $CONTAINER_NAME 2>/dev/null
        docker rm $CONTAINER_NAME 2>/dev/null
        echo "MCP Toolbox container cleaned up"
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|logs|clean}"
        echo ""
        echo "Commands:"
        echo "  start   - Start the MCP Toolbox container"
        echo "  stop    - Stop the MCP Toolbox container"
        echo "  restart - Restart the MCP Toolbox container"
        echo "  status  - Show container status"
        echo "  logs    - Show container logs"
        echo "  clean   - Stop and remove the container"
        exit 1
        ;;
esac
