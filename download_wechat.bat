@echo off
echo ========================================
echo  微信降级工具
echo  目标版本: 4.1.8.107 (wxauto4免费版兼容)
echo ========================================
echo.
echo 请先关闭微信，然后按任意键继续...
pause >nul

echo.
echo 正在下载微信 4.1.8.107...
echo 如果下载失败，请手动下载:
echo https://github.com/SiverKing/wechat4.0-windows-versions/releases/tag/v4.1.8.107
echo.

powershell -Command "Invoke-WebRequest -Uri 'https://github.com/SiverKing/wechat4.0-windows-versions/releases/download/v4.1.8.107/weixin_4.1.8.107.exe' -OutFile 'd:\Desktop\新建文件夹\wechat_auto_reply\weixin_4.1.8.107.exe'"

if exist "d:\Desktop\新建文件夹\wechat_auto_reply\weixin_4.1.8.107.exe" (
    echo.
    echo 下载完成！正在启动安装程序...
    echo 请在安装程序中选择"覆盖安装"，不会丢失聊天记录。
    echo.
    start "" "d:\Desktop\新建文件夹\wechat_auto_reply\weixin_4.1.8.107.exe"
) else (
    echo.
    echo 下载失败，请手动下载安装。
    echo.
)

pause
