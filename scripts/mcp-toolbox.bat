@echo off
REM MCP Toolbox Management Script for Windows
REM This script helps manage the MCP Toolbox Docker container

set CONTAINER_NAME=mcp-toolbox
set IMAGE=us-central1-docker.pkg.dev/database-toolbox/toolbox/toolbox:latest
set TOOLS_FILE=./tools.yaml

if "%1"=="start" (
    echo Starting MCP Toolbox container in HTTP mode...
    docker run -d --name %CONTAINER_NAME% -p 5001:5001 -v %TOOLS_FILE%:/app/tools.yaml %IMAGE% --tools-file /app/tools.yaml --address 0.0.0.0 --port 5001 --log-level DEBUG
    echo MCP Toolbox container started with name: %CONTAINER_NAME%
    echo Access at: http://localhost:5001
    echo Test with: curl http://localhost:5001/
) else if "%1"=="start-ui" (
    echo Starting MCP Toolbox container with UI...
    docker run -d --name %CONTAINER_NAME% -p 5000:5000 -v %TOOLS_FILE%:/app/tools.yaml %IMAGE% --tools-file /app/tools.yaml --ui
    echo MCP Toolbox container started with UI
    echo Access UI at: http://localhost:5000/ui
) else if "%1"=="start-both" (
    echo Starting MCP Toolbox container with both UI and debug ports...
    docker run -d --name %CONTAINER_NAME% -p 5000:5000 -p 5001:5001 -v %TOOLS_FILE%:/app/tools.yaml %IMAGE% --tools-file /app/tools.yaml --ui --address 0.0.0.0 --port 5001 --log-level DEBUG
    echo MCP Toolbox container started with both UI and debug ports
    echo UI at: http://localhost:5000/ui
    echo Debug at: http://localhost:5001
) else if "%1"=="stop" (
    echo Stopping MCP Toolbox container...
    docker stop %CONTAINER_NAME%
    echo MCP Toolbox container stopped
) else if "%1"=="restart" (
    echo Restarting MCP Toolbox container in HTTP mode...
    docker stop %CONTAINER_NAME% 2>nul
    docker rm %CONTAINER_NAME% 2>nul
    docker run -d --name %CONTAINER_NAME% -p 5001:5001 -v %TOOLS_FILE%:/app/tools.yaml %IMAGE% --tools-file /app/tools.yaml --address 0.0.0.0 --port 5001 --log-level DEBUG
    echo MCP Toolbox container restarted in HTTP mode
) else if "%1"=="status" (
    echo MCP Toolbox container status:
    docker ps | findstr %CONTAINER_NAME%
    echo.
    echo Port bindings:
    docker port %CONTAINER_NAME%
) else if "%1"=="logs" (
    echo MCP Toolbox container logs:
    docker logs %CONTAINER_NAME%
) else if "%1"=="test" (
    echo Testing MCP Toolbox connection...
    curl http://localhost:5001/ 2>nul
    if %errorlevel% equ 0 (
        echo MCP Toolbox is responding correctly!
    ) else (
        echo MCP Toolbox is not responding. Check logs with: %0 logs
    )
) else if "%1"=="clean" (
    echo Cleaning up MCP Toolbox container...
    docker stop %CONTAINER_NAME% 2>nul
    docker rm %CONTAINER_NAME% 2>nul
    echo MCP Toolbox container cleaned up
) else (
    echo Usage: %0 {start^|start-ui^|start-both^|stop^|restart^|status^|logs^|test^|clean}
    echo.
    echo Commands:
    echo   start      - Start in debug mode (port 5001)
    echo   start-ui   - Start with UI (port 5000)
    echo   start-both - Start with both UI and debug ports
    echo   stop       - Stop the MCP Toolbox container
    echo   restart    - Restart the MCP Toolbox container
    echo   status     - Show container status and port bindings
    echo   logs       - Show container logs
    echo   test       - Test if MCP Toolbox is responding
    echo   clean      - Stop and remove the container
)
