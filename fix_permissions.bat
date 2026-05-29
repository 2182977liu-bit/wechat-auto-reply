@echo off
echo ========================================
echo 修复 Python comtypes 库权限问题
echo ========================================
echo.
echo 正在以管理员权限修复...
powershell -Command "Start-Process 'cmd' -ArgumentList '/c icacls \"C:\Users\青松\AppData\Local\Programs\Python\Python310\Lib\site-packages\comtypes\gen\" /grant \"Everyone:(OI)(CI)F\" /T & pause' -Verb RunAs"
echo.
echo 修复完成后，请重新启动程序：
echo   python main.py --web
echo.
pause
