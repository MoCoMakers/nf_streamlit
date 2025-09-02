@echo off
REM MCP Toolbox Management Script for Windows
REM This script helps manage the MCP Toolbox Docker container

set CONTAINER_NAME=mcp-toolbox
set IMAGE=us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest
set TOOLS_FILE=./tools.yaml

if "%1"=="start" (
    echo Starting MCP Toolbox container...
    docker run -d --name %CONTAINER_NAME% -p 5000:5000 -v %TOOLS_FILE%:/app/tools.yaml %IMAGE% --tools-file /app/tools.yaml
    echo MCP Toolbox container started with name: %CONTAINER_NAME%
) else if "%1"=="stop" (
    echo Stopping MCP Toolbox container...
    docker stop %CONTAINER_NAME%
    echo MCP Toolbox container stopped
) else if "%1"=="restart" (
    echo Restarting MCP Toolbox container...
    docker stop %CONTAINER_NAME% 2>nul
    docker rm %CONTAINER_NAME% 2>nul
    docker run -d --name %CONTAINER_NAME% -p 5000:5000 -v %TOOLS_FILE%:/app/tools.yaml %IMAGE% --tools-file /app/tools.yaml
    echo MCP Toolbox container restarted
) else if "%1"=="status" (
    echo MCP Toolbox container status:
    docker ps | findstr %CONTAINER_NAME%
) else if "%1"=="logs" (
    echo MCP Toolbox container logs:
    docker logs %CONTAINER_NAME%
) else if "%1"=="clean" (
    echo Cleaning up MCP Toolbox container...
    docker stop %CONTAINER_NAME% 2>nul
    docker rm %CONTAINER_NAME% 2>nul
    echo MCP Toolbox container cleaned up
) else (
    echo Usage: %0 {start^|stop^|restart^|status^|logs^|clean}
    echo.
    echo Commands:
    echo   start   - Start the MCP Toolbox container
    echo   stop    - Stop the MCP Toolbox container
    echo   restart - Restart the MCP Toolbox container
    echo   status  - Show container status
    echo   logs    - Show container logs
    echo   clean   - Stop and remove the container
)
