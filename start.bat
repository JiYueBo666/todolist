@echo off
chcp 65001 >nul
echo ================================
echo   TodoList - Docker 一键启动
echo ================================
echo.
echo 访问地址: http://localhost:8000
echo API 文档: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 停止
echo ================================
echo.
docker compose up --build
pause
