@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

set "frame1=     ██╗    █████╗    ██████╗   ██╗   ██╗  ██╗   ███████╗   "
set "frame2=     ██║   ██╔══██╗   ██╔══██╗  ██║   ██║  ██║   ██╔════╝   "
set "frame3=     ██║   ███████║   ██████╔╝  ██║   ██║  ██║   ███████╗   "
set "frame4=██   ██║   ██╔══██║   ██╔══██╗  ╚██╗ ██╔╝  ██║   ╚════██║   "
set "frame5=╚█████╔╝██╗██║  ██║██╗██║  ██║██╗╚████╔╝██╗██║██╗███████║██╗"
set "frame6= ╚════╝ ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚═╝ ╚═══╝ ╚═╝╚═╝╚═╝╚══════╝╚═╝"

cls
echo.
echo %frame1%
timeout /t 0 >nul
echo %frame2%
timeout /t 0 >nul
echo %frame3%
timeout /t 0 >nul
echo %frame4%
timeout /t 0 >nul
echo %frame5%
timeout /t 0 >nul
echo %frame6%
timeout /t 2 >nul
echo 请等待……

claude 阅读README.md，汇报今天应该完成的内容供我选择；每次执行完成后修改README.md文件中的完成进度；使用中文思考和回复

cmd /k