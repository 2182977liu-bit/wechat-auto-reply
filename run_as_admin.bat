@echo off
echo 正在以管理员权限启动微信自动回复...
powershell -Command "Start-Process 'C:\Users\青松\AppData\Local\Programs\Python\Python310\python.exe' -ArgumentList 'main.py --web' -Verb RunAs -WorkingDirectory '%~dp0'"
echo 启动完成！请在浏览器中访问 http://localhost:5000
pause
