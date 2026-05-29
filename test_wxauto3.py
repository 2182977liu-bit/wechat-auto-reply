"""直接测试wxauto4连接 - 使用窗口句柄"""
import os
import ctypes
from pathlib import Path

# 设置comtypes缓存
user_cache = Path.home() / ".comtypes_cache"
user_cache.mkdir(exist_ok=True)
os.environ["COMTYPES_CACHE"] = str(user_cache)

import comtypes
import comtypes.client
comtypes.client.gen_dir = str(user_cache)
comtypes.gen.__path__ = [str(user_cache)]

# 查找微信窗口
hwnd = ctypes.windll.user32.FindWindowW(None, "微信")
print(f"微信窗口句柄: {hwnd}")

if hwnd:
    # 检查窗口是否可见
    visible = ctypes.windll.user32.IsWindowVisible(hwnd)
    print(f"窗口可见: {visible}")
    
    # 检查窗口是否最小化
    iconic = ctypes.windll.user32.IsIconic(hwnd)
    print(f"窗口最小化: {iconic}")
    
    if iconic:
        print("窗口已最小化，正在恢复...")
        ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
        import time
        time.sleep(1)
    
    # 激活窗口
    print("正在激活窗口...")
    ctypes.windll.user32.SetForegroundWindow(hwnd)
    import time
    time.sleep(0.5)

print("\n正在导入wxauto4...")
from wxauto4 import WeChat

print("正在连接微信...")
try:
    wx = WeChat()
    print("连接成功！")
    
    sessions = wx.GetSessionList()
    print(f"会话列表: {sessions}")
except Exception as e:
    print(f"错误: {e}")
    
    # 尝试使用窗口句柄
    print("\n尝试使用窗口句柄直接连接...")
    try:
        wx = WeChat(hwnd=hwnd)
        print("连接成功！")
    except Exception as e2:
        print(f"错误: {e2}")
